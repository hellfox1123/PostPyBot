import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import BOT_TOKEN, DATABASE_PATH
from database import db
from telegram_client import telegram_client
from scheduler import Scheduler
from poster import Poster
from handlers import start, interval, caption, mode, schedule, service, actions, auth
from utils import logger, send_admin_notification

async def main():
    """Головна функція"""
    
    # Створюємо директорію для бази якщо її немає
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Ініціалізуємо базу даних
    await db.init()
    logger.info("База даних ініціалізована")
    
    # Створюємо бота
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Ініціалізуємо Telethon клієнт
    is_authorized = await telegram_client.init(bot)
    
    if not is_authorized:
        logger.warning("Telethon не авторизовано. Використайте команду /auth")
        await send_admin_notification(
            bot,
            "⚠️ Telethon не авторизовано!\n\n"
            "Використайте команду /auth для авторизації."
        )
    
    # Ініціалізуємо Poster
    global poster
    from poster import poster as poster_instance
    poster_instance = Poster(bot)
    
    # Створюємо диспетчер
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Реєструємо роутери
    dp.include_router(auth.router)
    dp.include_router(start.router)
    dp.include_router(interval.router)
    dp.include_router(caption.router)
    dp.include_router(mode.router)
    dp.include_router(schedule.router)
    dp.include_router(service.router)
    dp.include_router(actions.router)
    
    # Створюємо та запускаємо планувальник
    global scheduler
    scheduler = Scheduler(bot)
    
    if is_authorized:
        await scheduler.start()
        logger.info("Бот запущено")
    else:
        logger.warning("Бот запущено в режимі очікування авторизації")
    
    # Запускаємо polling
    try:
        await dp.start_polling(bot)
    finally:
        if is_authorized:
            await scheduler.stop()
        await telegram_client.disconnect()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинено")