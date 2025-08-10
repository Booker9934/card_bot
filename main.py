import asyncio
import logging
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from Handlers import card_create, delete_card, learn, show_cards, start
from database import async_main
storage = MemoryStorage()

load_dotenv()
BOT_TOKEN=os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


async def main():
    await async_main()
    dp.include_router(card_create.router_create)
    dp.include_router(delete_card.router_delete)
    dp.include_router(learn.router_learn)
    dp.include_router(show_cards.router_show)
    dp.include_router(start.router_start)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')