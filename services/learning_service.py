from card_bot.models.models import Card
from card_bot.database import async_session
from card_bot.states import CardState

from aiogram.types import Message
from aiogram.fsm.context import FSMContext

import time
from sqlalchemy import select

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
                card = await session.scalar(select(Card).where(Card.id == indexs[current_index]))

                if time.time() - float(card.time) > 3600 * card.time:
                    if card.photo_id == "Без фото":
                        await message.answer(f"Слово: {card.front}.\nНапишите перевод слова")

                        card.time = time.time()

                        await state.set_state(CardState.translate)
                    else:
                        await message.answer_photo(photo=card.photo_id,
                                                   caption=f"Слово: {card.front}.\nНапишите перевод слова")
                        await state.set_state(CardState.translate)
                else:
                    card.hours *= 2
                    await state.update_data(current_index=current_index + 1)
                    await show_current_card(message, state)
    except IndexError:
            await message.answer("Вы прошли все карточки. Приходите позже")
            await state.clear()
            await state.update_data(current_index=current_index, indexs=indexs, cards=cards)
            return