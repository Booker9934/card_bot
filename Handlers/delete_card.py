from aiogram import F, Router
from aiogram.types import Message
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command

from card_bot.states import CardDelete
from card_bot.database import async_session
from card_bot.models.models import Card

from sqlalchemy import select

router_delete = Router()

@router_delete.message(F.text.lower() == "удалить карточку")
@router_delete.message(Command("delete_card"))
async def delete(message: Message, state: FSMContext):
    await message.answer("Напишите id карточки")
    await state.set_state(CardDelete.delete)

@router_delete.message(F.text, CardDelete.delete)
async def deleting(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.reply("Нужно ввести число")
        await state.clear()
        return
    if int(message.text) <= 0:
        await message.reply("id карточки может быть только больше 0")
        await state.clear()
        return

    card_id = int(message.text)

    async with async_session() as session:
        card = await session.scalar(select(Card).where(Card.id == card_id))

        if not card:
            await state.clear()
            await message.reply("Карточки с таким id не существует")

        record_to_delete = await session.get(Card, card_id)

        await session.delete(record_to_delete)
        await session.commit()
        await message.reply("✅ Карточка удалена")

        await state.clear()
