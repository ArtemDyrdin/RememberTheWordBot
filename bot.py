import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Подключаем переменные
from app.config import settings

# Импортируем инициализацию БД и роутеры
from app.db.init_db import init_database
from app.handlers.start import core_router
from app.handlers.add_word import add_word_router
from app.handlers.review import review_router


BOT_TOKEN = settings.BOT_TOKEN

async def main() -> None:
    # 1. Инициализируем базу данных (создаст local.db и таблицы, если их нет)
    logging.info("Инициализация базы данных...")
    await init_database()

    # 2. Настраиваем бота и диспетчер
    bot = Bot(
        token=BOT_TOKEN, 
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # 3. Регистрируем роутеры
    dp.include_router(core_router)
    dp.include_router(add_word_router)
    dp.include_router(review_router)

    # 4. Запускаем бота
    logging.info("Запуск бота...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())