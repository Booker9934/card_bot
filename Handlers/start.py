from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart

router_start = Router()

@router_start.message(CommandStart())
async def cmd_start(message: Message):
    welcome_message = (
        f"Привет, {message.from_user.username}!\n\n"
        "Я бот для изучения чего-либо по карточкам.\n"
        "Используй команды:\n"
        "/create_card - создать новую карточку\n"
        "/start_learn - начать обучение\n"
        "/show_cards - посмотреть свои карточки\n"
        "/delete_card - удалить карточку"
    )

    await message.answer(welcome_message)