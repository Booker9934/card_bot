from aiogram import Router, F
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from ..database import async_session
from ..models.models import Card
from ..keyboards.keyboards import builder_markup, back_from_groups_kb

from sqlalchemy import select

router_show = Router()

@router_show.message(Command('show_cards'))
@router_show.message(F.text.lower() == "показать карты")
async def start_show_cards(message: Message):
    """
    Показывает все группы
    """
    async with async_session() as session:
        cards = await session.scalars(select(Card))
        keyboard = await builder_markup(cards)

        await message.reply("Выберете группу", reply_markup=keyboard)

@router_show.callback_query(F.data.startswith("Группа "))
async def show_cards(callback: CallbackQuery):
    """
    Показ всех карточек, когда человек выбрал группу
    """
    async with async_session() as session:
        group = callback.data.split('Группа ')[1]
        cards = await session.scalars(select(Card).where(Card.group==group))
        mes = ""


        for card in cards:
            mes += f"{card.back} {card.id} {card.group}\n"

        await callback.message.edit_text(mes, reply_markup=back_from_groups_kb)

@router_show.callback_query(F.data == "All")
async def cl(callback: CallbackQuery):
    """
    Показывает все карточки из всех групп
    """
    async with async_session() as session:
        try:
            cards = await session.scalars(select(Card))
            mes = ""

            for card in cards:
                mes += f"{card.back} {card.id} {card.group}\n"

            await callback.message.edit_text(mes, reply_markup=back_from_groups_kb)
        except TelegramBadRequest:
            await callback.message.answer("Сначала создайте карточку")

@router_show.callback_query(F.data == "back")
async def back_to_groups(callback: CallbackQuery):
    """
    Возвращает из просмотра всех карточек в просмотр всех групп
    """
    async with async_session() as session:
        try:
            cards = await session.scalars(select(Card))
            keyboard = await builder_markup(cards)

            await callback.message.edit_text("Выберете группу", reply_markup=keyboard)
        except TelegramBadRequest:
            await callback.message.answer("Сначала создайте карточку")