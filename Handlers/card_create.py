from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import Command
from aiogram.types import Message

from services.card_service import create_card
from keyboards.keyboards import main_menu
from states import CreateCardStates

from sqlalchemy import select

router_create = Router()

@router_create.message(Command("create_card"))
@router_create.message(F.text.lower() == "создать карточку")
async def cmd_create_card(message: Message, state: FSMContext):
    """
    Начало создания карточки
    """
    await message.answer("Введите слово (передняя сторона)")
    await state.set_state(CreateCardStates.waiting_for_front)

@router_create.message(CreateCardStates.waiting_for_front)
async def record_front(message: Message, state: FSMContext):
    """
    Обработка передней стороны карточки
    """
    await state.update_data(front=message.text)
    await message.answer("Введите перевод (задняя сторона)")
    await state.set_state(CreateCardStates.waiting_for_back)

@router_create.message(CreateCardStates.waiting_for_back)
async def record_back(message: Message, state: FSMContext):
    """
    Обработка задней стороны карточки
    """
    await state.update_data(back=message.text)
    await message.answer('Введите название группы или "-" для пропуска')
    await state.set_state(CreateCardStates.waiting_for_group)

@router_create.message(CreateCardStates.waiting_for_group)
async def record_group(message: Message, state: FSMContext):
    """
    Обработка группы
    """
    await state.update_data(group=message.text if message.text != "-" else "Без группы")
    await message.answer('Отправьте фото карточки или "-" для пропуска')
    await state.set_state(CreateCardStates.waiting_for_photo_id)

@router_create.message(CreateCardStates.waiting_for_photo_id)
async def record_photo_id(message: Message, state: FSMContext):
    """
    Обработка фото карточки
    """
    if message.text == "-":
        await state.update_data(photo_id="Без фото")
    else:
        try:
            await state.update_data(photo_id=message.photo[-1].file_id)
        except TypeError:
            await message.reply("Нужно отправить фото или '-' для пропуска")

    data = await state.get_data()

    #Создаём карточку
    card = await create_card(
            front=data['front'],
            back=data['back'],
            photo_id=data['photo_id'],
            group=data["group"],
        )

    if card.photo_id == "Без фото":
        await message.answer(f"""✅ Карточка создана
📌Передняя сторона: {card.front}
📌Задняя сторона: {card.back}
🗂Группа: {card.group}""",
                            reply_markup=main_menu()
                            )
    else:
        await message.answer_photo(photo=card.photo_id,
                                    caption=f"""✅ Карточка создана
📌Передняя сторона: {card.front}
📌Задняя сторона: {card.back}
🗂Группа: {card.group}""",
                                    reply_markup=main_menu())

    await state.clear()
