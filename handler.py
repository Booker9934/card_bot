import time
import asyncio
from traceback import print_tb

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from card_bot.db_card import Cards, async_session
from sqlalchemy import select
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()



class Card(StatesGroup):
    translate = State()

@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.reply("Я бот для создания карточек на любые темы. Вот мои команды:\nПока не придумал)")




@router.message(Card.translate)
async def ms(message: Message, state: FSMContext):
    """
    Проверка на правильность ответа
    После правильного ответа карточка будет показываться в следующий раз в 2 раза дольше чем предыдущий
    После неправильного ответа карточка будет показываться через час
    """
    data = await state.get_data()
    current_index = data['current_index']
    indexs = data['indexs']
    async with async_session() as session:
        card = await session.scalar(select(Cards).where(Cards.id == indexs[current_index]))
        if message.text.lower() == card.text_back.lower():
            kb_info = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Посмотреть обратную сторону", callback_data="watch_back")]])
            await message.answer("Вы ответили правильно", reply_markup=kb_info)
            card.level *= 2
            await session.commit()
        else:
            kb_info = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Посмотреть обратную сторону", callback_data="watch_back")]])
            await message.answer("Вы ответили Неправильно", reply_markup=kb_info)

            card.level = 1
            await session.commit()
        card.time = time.time()
        await session.commit()
        await state.update_data(current_index=current_index+1)
        await show_current_card(message, state)

@router.message()
async def ms(message: Message, state: FSMContext):
    async with async_session() as session:
        #Создание карточки без фото
        if message.text.lower().startswith('создать карточку'):
                session.add(Cards(text_front=message.text.split('\n')[1], text_back=message.text.split('\n')[2], photo_id="Без фото", time=time.time(), level=1, group=message.text.split('\n')[3].split('Группа ')[1] if "группа" in message.text.lower() else "Без группы"))
                await session.commit()
                await message.reply("Карточка создана")

        #Начало обучения
        if message.text.lower().startswith("начать"):
            cards = await session.scalars(select(Cards))
            cards_list = cards.all()
            indexs = []
            for card in cards_list:
                if time.time() - float(card.time) > 3600 * card.level:
                    indexs.append(card.id)
            await state.update_data(cards=cards_list, current_index=0, indexs=indexs)
            await show_current_card(message, state)

        #Показ всех групп
        if message.text.lower() == "показать карты":
            builder = InlineKeyboardBuilder()
            cards = await session.scalars(select(Cards))
            groups = []
            for card in cards:
                if card.group not in groups:
                    groups.append(card.group)
                    builder.button(text=f'{card.group}', callback_data=f"Группа {card.group}")
            builder.button(text="Все группы", callback_data='All')
            builder.adjust(1)
            keyboard = builder.as_markup()
            await message.reply("Выберете группу", reply_markup=keyboard)

        #Удаление карточек
        if message.text.lower().startswith('удалить'):
            i = message.text.lower().split('удалить ')[1]
            record_to_delete = await session.get(Cards, i)
            await session.delete(record_to_delete)
            await session.commit()
            await message.reply("Карточка удалена")

@router.message(F.photo)
async def ms(message: Message):
    #Создание карточки с фото
    if message.caption.lower().startswith('создать карточку'):
        async with async_session() as session:
            session.add(Cards(text_front=message.caption.split('\n')[1], text_back=message.caption.split('\n')[2], photo_id=message.photo[-1].file_id, time=time.time(), level=1, group=message.caption.split('\n')[3] if "группа" in message.caption.lower() else "Без группы"))
            await session.commit()
            await message.reply("Карточка создана")

async def show_current_card(message: Message, state: FSMContext):
    #Показывает карточку после команды "Начать"
    data = await state.get_data()
    cards = data['cards']
    current_index = data['current_index']
    indexs = data['indexs']
    if current_index > indexs[-1]:
        await message.answer("Все карточки пройдены, приходите позже")
        await state.clear()
        await state.update_data(current_index=current_index, indexs=indexs, cards=cards)
        return
    async with async_session() as session:
        try:
            card = await session.scalar(select(Cards).where(Cards.id == indexs[current_index]))
            if time.time() - float(card.time) > 3600 * card.level:
                if card.photo_id == "Без фото":
                    await message.answer(f"Слово: {card.text_front}.\nНапишите перевод слова")
                    card.time = time.time()
                    await state.set_state(Card.translate)
                else:
                    await message.answer_photo(photo=card.photo_id, caption=f"Слово: {card.text_front}.\nНапишите перевод слова")
                    await state.set_state(Card.translate)
            else:
                card.level *= 2
                await state.update_data(current_index=current_index + 1)
                await show_current_card(message, state)
        except IndexError:
            await message.answer("Вы прошли все карточки. Приходите позже")
            await state.clear()
            await state.update_data(current_index=current_index, indexs=indexs, cards=cards)
            return

@router.callback_query()
async def cl(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        #Показ всех карточек, когда человек выбрал группу
        if callback.data.startswith("Группа "):
                group = callback.data.split('Группа ')[1]
                cards = await session.scalars(select(Cards).where(Cards.group==group))
                mes = ""
                kb_back = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Вернуться", callback_data="back")]])
                for card in cards:
                    mes += f"{card.text_back} {card.id} {card.group}\n"
                await callback.message.edit_text(mes, reply_markup=kb_back)

        #Возвращает из просмотра всех карточек в просмотр всех групп
        if callback.data == "back":
            builder = InlineKeyboardBuilder()
            cards = await session.scalars(select(Cards))
            groups = []
            for card in cards:
                if card.group not in groups:
                    groups.append(card.group)
                    builder.button(text=f'{card.group}', callback_data=f"Группа {card.group}")
            builder.button(text="Все группы", callback_data='All')
            builder.adjust(1)
            keyboard = builder.as_markup()
            await callback.message.edit_text("Выберете группу", reply_markup=keyboard)

        #Показывает все карточки из всех групп
        if callback.data == "All":
            cards = await session.scalars(select(Cards))
            mes = ""
            kb_back = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Вернуться", callback_data="back")]])
            for card in cards:
                mes += f"{card.text_back} {card.id} {card.group}\n"
            await callback.message.edit_text(mes, reply_markup=kb_back)

        #Показывает доп информацию после правильного или неправильного ответа
        if callback.data == "watch_back":
            data = await state.get_data()
            current_index = data['current_index']
            indexs = data['indexs']
            card = await session.scalar(select(Cards).where(Cards.id == indexs[current_index-1]))
            tim = (card.level * 3600 - (time.time()-float(card.time))) / 3600
            await callback.message.edit_text(f"{card.text_back}\nПовторениее карточки будет через {tim} часов")
    # async with async_session() as session:
    #     i = await state.get_data()
    #     card = await session.scalar(select(Cards).where(Cards.id == i['index']))
    #     print(card.text_back.lower())
    #     print(message.text.lower())
    #     if card.text_back.lower() == message.text.lower():
    #         kb_info = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Посмотреть обратную сторону", callback_data="watch_back")]])
    #         await message.answer("Вы ответили правильно", reply_markup=kb_info)
    #         await state.clear()