from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from datetime import datetime
from card_bot.database import Base

class Card(Base):
    __tablename__ = "cards"

    id: Mapped[int] = mapped_column(primary_key=True)
    front: Mapped[str] = mapped_column()
    back: Mapped[str] = mapped_column()
    photo_id: Mapped[str] = mapped_column()
    time: Mapped[float] = mapped_column() # Время в которое была испльзована карточка в последний раз
    hours: Mapped[int] = mapped_column() # Время, через которое можно будет использовать карточку
    group: Mapped[str] = mapped_column()
