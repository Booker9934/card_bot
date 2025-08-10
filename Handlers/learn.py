from aiogram import F, Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from ..services.learning_service import show_current_card
from ..database import async_session
from ..models.models import Card
from ..states import CardState
from ..keyboards.keyboards import back_info

from sqlalchemy import select
import time


router_learn = Router()

@router_learn.message(Command("start_learn"))
@router_learn.message(F.text.lower() == "начать обучение")
async def start_learn(message: Message, state: FSMContext):
    """
        Начинает показ карточек
    """
    async with async_session() as session:

        cards = await session.scalars(select(Card))
        cards_list = cards.all()
        indexs = []  # Индексы карточек, которые нужно показать

        for card in cards_list:
            if time.time() - float(card.time) > 3600 * card.hours:
                indexs.append(card.id)

        await state.update_data(cards=cards_list,
                                current_index=0,
                                indexs=indexs)

        await show_current_card(message, state)

@router_learn.message(CardState.translate, F.text)
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
        card = await session.scalar(select(Card).where(Card.id == indexs[current_index]))

        back_info_kb = back_info()
        if message.text.lower() == card.back.lower():
            card.hours *= 2
            card.time = time.time()
            await session.commit()

            await message.answer("Вы ответили правильно", reply_markup=back_info_kb)
        else:
            card.hours = 1
            card.time = time.time()
            await session.commit()

            await message.answer("Вы ответили Неправильно", reply_markup=back_info_kb)

        await state.update_data(current_index=current_index+1)
        await show_current_card(message, state)

@router_learn.message(CardState.translate, F.photo)
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
        card = await session.scalar(select(Card).where(Card.id == indexs[current_index]))

        back_info_kb = back_info()
        if message.caption.lower() == card.back.lower():
            card.hours *= 2
            card.time = time.time()
            await session.commit()

            await message.answer("Вы ответили правильно", reply_markup=back_info_kb)

        else:
            card.hours = 1
            card.time = time.time()
            await session.commit()

            await message.answer("Вы ответили Неправильно", reply_markup=back_info_kb)

        await session.commit()
        await state.update_data(current_index=current_index+1)
        await show_current_card(message, state)

@router_learn.callback_query(F.data == "watch_back")
async def watch_back(callback: CallbackQuery, state: FSMContext):
    """
    Показывает доп информацию после правильного или неправильного ответа
    """
    async with async_session() as session:
        data = await state.get_data()
        current_index = data['current_index']
        indexs = data['indexs']
        print(current_index)
        print(indexs)
        card = await session.scalar(select(Card).where(Card.id == indexs[current_index - 1]))
        tim = (card.hours * 3600 - (time.time() - float(card.time))) / 3600

        await callback.message.edit_text(f"{card.back}\nПовторениее карточки будет через {tim} часов")