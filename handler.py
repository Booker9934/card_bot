import time
import asyncio

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy import select
from db_card import Cards, async_session

router = Router()

class Card(StatesGroup):
    translate = State()

@router.message(Command('start'))
async def cmd_start(message: Message):
    await message.reply("Я бот для создания карточек на любые темы.)")

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

@router.message(F.text.lower().startswith('создать карточку'))
async def create_card(message: Message, state: FSMContext):
    """Обрабатывает создание новой карточки без фото.

    Формат сообщения:
    Создать карточку
    Передняя сторона
    Оборотная сторона
    Группа название_группы (опционально)
    """
    try:
        async with async_session() as session:

            splited_text = message.text.split("\n")
            text_front = splited_text[1]
            text_back = splited_text[2]
            group = splited_text[3].split('группа ') if "группа " in message.text else "без группы"

            session.add(Cards(
                text_front=text_front,
                text_back=text_back,
                photo_id="Без фото",
                time=time.time(),
                level=1,
                group=group))

            await session.commit()
            await message.reply("✅ Карточка успешно создана")
    except IndexError:
        await message.reply(
            "❌ Неверный формат. Используйте:\nСоздать карточку\nПередняя сторона\nОборотная сторона\nГруппа название (опционально)")
    except Exception as e:
        print(f"Ошибка при создании карточки: {e}")
        await message.reply("❌ Произошла ошибка при создании карточки")

@router.message(F.text.lower() == "начать")
async def start(message: Message, state: FSMContext):
    """
    Начинает показ карточек
    """
    async with async_session() as session:

        cards = await session.scalars(select(Cards))
        cards_list = cards.all()
        indexs = [] # Индексы карточек, которые нужно показать

        for card in cards_list:
            if time.time() - float(card.time) > 3600 * card.level:
                indexs.append(card.id)

        await state.update_data(cards=cards_list,
                                current_index=0,
                                indexs=indexs)

        await show_current_card(message, state)

@router.message(F.text.lower() == "показать карты")
async def show_cards(message: Message, state: FSMContext):
    """
    Показывает все группы
    """
    async with async_session() as session:

        if message.text.lower() == "показать карты":

            cards = await session.scalars(select(Cards))
            keyboard = await builder_markup(cards)

            await message.reply("Выберете группу", reply_markup=keyboard)

@router.message(F.text.lower().startswith('удалить'))
async def delete_card(message: Message, state: FSMContext):
    """
    Удаляет карточку по id.

    Формат:
    Удалить [id]
    """
    try:
        async with async_session() as session:

            card_id = message.text.lower().split('удалить ')[1]
            record_to_delete = await session.get(Cards, card_id)

            await session.delete(record_to_delete)
            await session.commit()
            await message.reply("✅ Карточка удалена")

    except UnmappedInstanceError:
        await message.reply("❌ Не удалось удалить карточку\nПридерживайтесь форматы\nУдалить [id]")

@router.message(F.photo and F.text.lower().startswith("создать карточку"))
async def create_card_with_photo(message: Message):
    """
    Создаёт карточки с фото
    """
    try:
        async with async_session() as session:
            splited_text = message.text.split("\n")
            text_front = splited_text[1]
            text_back = splited_text[2]
            photo_id = message.photo[-1].file_id
            group = splited_text[3].split('группа ') if "группа " in message.text else "без группы"

            session.add(Cards(
                text_front=text_front,
                text_back=text_back,
                photo_id=photo_id,
                time=time.time(),
                level=1,
                group=group))
            await session.commit()
            await message.reply("✅ Карточка успешно создана")
    except IndexError:
        await message.reply(
            "❌ Неверный формат. Используйте:\nСоздать карточку\nПередняя сторона\nОборотная сторона\nГруппа название (опционально)")
    except Exception as e:
        print(f"Ошибка при создании карточки: {e}")
        await message.reply("❌ Произошла ошибка при создании карточки")

async def show_current_card(message: Message, state: FSMContext):
    """
    Показывает карты после команды "Начать"
    """

    data = await state.get_data()
    cards = data['cards']
    current_index = data['current_index']
    indexs = data['indexs']

    try:
        if current_index > indexs[-1]:
            await message.answer("Все карточки пройдены, приходите позже")
            await state.clear()
            await state.update_data(current_index=current_index,
                                    indexs=indexs,
                                    cards=cards)
            return

        async with async_session() as session:
                card = await session.scalar(select(Cards).where(Cards.id == indexs[current_index]))

                if time.time() - float(card.time) > 3600 * card.level:
                    if card.photo_id == "Без фото":
                        await message.answer(f"Слово: {card.text_front}.\nНапишите перевод слова")

                        card.time = time.time()

                        await state.set_state(Card.translate)
                    else:
                        await message.answer_photo(photo=card.photo_id,
                                                   caption=f"Слово: {card.text_front}.\nНапишите перевод слова")
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

async def builder_markup(cards):
    """
    Создают клавиатуру из групп
    """

    builder = InlineKeyboardBuilder()
    groups = []

    for card in cards:
        if card.group not in groups:
            groups.append(card.group)
            builder.button(text=f'{card.group}', callback_data=f"Группа {card.group}")

    builder.button(text="Все группы", callback_data='All')
    builder.adjust(1)

    return builder.as_markup()

@router.callback_query(F.data.startswith("Группа "))
async def show_cards(callback: CallbackQuery, state: FSMContext):
    """
    Показ всех карточек, когда человек выбрал группу
    """
    async with async_session() as session:

        group = callback.data.split('Группа ')[1]
        cards = await session.scalars(select(Cards).where(Cards.group==group))
        mes = ""

        kb_back = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Вернуться", callback_data="back")]])

        for card in cards:
            mes += f"{card.text_back} {card.id} {card.group}\n"

        await callback.message.edit_text(mes, reply_markup=kb_back)

@router.callback_query(F.data == "back")
async def back_to_groups(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает из просмотра всех карточек в просмотр всех групп
    """
    async with async_session() as session:
        try:
                cards = await session.scalars(select(Cards))
                keyboard = builder_markup(cards)

                await callback.message.edit_text("Выберете группу", reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer("Сначала создайте карточку")

@router.callback_query(F.data == "All")
async def cl(callback: CallbackQuery, state: FSMContext):
    """
    Показывает все карточки из всех групп
    """
    async with async_session() as session:
        try:
            cards = await session.scalars(select(Cards))
            mes = ""
            kb_back = InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="Вернуться", callback_data="back")]])

            for card in cards:
                mes += f"{card.text_back} {card.id} {card.group}\n"

            await callback.message.edit_text(mes, reply_markup=kb_back)
        except TelegramBadRequest:
            await callback.message.answer("Сначала создайте карточку")

@router.callback_query(F.data == "watch_back")
async def cl(callback: CallbackQuery, state: FSMContext):
    """
    Показывает доп информацию после правильного или неправильного ответа
    """
    async with async_session() as session:
        if callback.data == "watch_back":
            data = await state.get_data()
            current_index = data['current_index']
            indexs = data['indexs']

            card = await session.scalar(select(Cards).where(Cards.id == indexs[current_index-1]))
            tim = (card.level * 3600 - (time.time()-float(card.time))) / 3600

            await callback.message.edit_text(f"{card.text_back}\nПовторениее карточки будет через {tim} часов")