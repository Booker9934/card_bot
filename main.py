import asyncio
import logging
from aiogram import Bot, Dispatcher
from db_card import async_main
from handler import router
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
storage = MemoryStorage()

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