from sqlalchemy import BigInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, create_async_engine, async_sessionmaker

engine = create_async_engine(url='sqlite+aiosqlite:///card_db.db.sqlite3')
async_session = async_sessionmaker(engine)

class Base(AsyncAttrs, DeclarativeBase):
    pass

class Cards(Base):
    __tablename__ = 'cards'
    id: Mapped[int] = mapped_column(primary_key=True)
    text_front = mapped_column(String)
    text_back = mapped_column(String)
    photo_id = mapped_column(String)
    time = mapped_column(String)
    level: Mapped[int] = mapped_column()
    group = mapped_column(String, default="Без группы")

async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)