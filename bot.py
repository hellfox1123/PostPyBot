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
    
    # Ініціалізуємо Poster
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
    
    # Створюємо планувальник
    global scheduler
    scheduler = Scheduler(bot)
    
    if is_authorized:
        await scheduler.start()
        logger.info("✅ Бот запущено і готовий до роботи")
        await send_admin_notification(
            bot,
            "✅ <b>Бот запущено!</b>\n\n"
            "Telethon авторизовано, планувальник працює.",
            parse_mode="HTML"
        )
    else:
        logger.warning("⚠️ Telethon не авторизовано - бот в режимі очікування")
        await send_admin_notification(
            bot,
            "⚠️ <b>Telethon не авторизовано!</b>\n\n"
            "Використайте команду /auth для авторизації.",
            parse_mode="HTML"
        )
    
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
