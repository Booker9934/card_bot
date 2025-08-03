import asyncio
import logging
from dotenv import load_dotenv
import os

from aiogram import Bot, Dispatcher
from db_card import async_main
from handler import router
from aiogram.fsm.storage.memory import MemoryStorage
storage = MemoryStorage()

load_dotenv()
BOT_TOKEN=os.getenv('BOT_TOKEN')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)


async def main():
    await async_main()
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('exit')