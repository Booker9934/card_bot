from sqlalchemy import select

from card_bot.database import async_session
from card_bot.models.models import Card

import time

async def create_card(
        front: str,
        back: str,
        photo_id: str,
        group: str
) -> Card:
    """
    Создаёт новую карточку в бд
    """
    async with async_session() as session:
            card = Card(
                front=front.strip(),
                back=back.strip(),
                time=time.time(),
                group=group.strip(),
                hours=1,
                photo_id=photo_id
            )

            session.add(card)
            await session.commit()
            await session.refresh(card)
            return card