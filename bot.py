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
import scheduler as scheduler_module  # <-- ЗМІНЕНО
from scheduler import Scheduler
import poster as poster_module        # <-- ЗМІНЕНО
from poster import Poster
from handlers import start, interval, caption, mode, schedule, service, actions, auth
from utils import logger, send_admin_notification


async def main():
    """Головна функція"""
    
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    await db.init()
    logger.info("База даних ініціалізована")
    
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    is_authorized = await telegram_client.init(bot)
    
    # Правильно зберігаємо Poster в модуль
    poster_module.poster = Poster(bot)
    logger.info("Poster ініціалізовано")
    
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    dp.include_router(auth.router)
    dp.include_router(start.router)
    dp.include_router(interval.router)
    dp.include_router(caption.router)
    dp.include_router(mode.router)
    dp.include_router(schedule.router)
    dp.include_router(service.router)
    dp.include_router(actions.router)
    
    # Правильно зберігаємо Scheduler в модуль
    scheduler_module.scheduler = Scheduler(bot)
    logger.info("Scheduler ініціалізовано")
    
    if is_authorized:
        await scheduler_module.scheduler.start()
        logger.info("✅ Бот запущено і готовий до роботи")
        await send_admin_notification(
            bot,
            "✅ <b>Бот запущено!</b>\n\n"
            "Telethon авторизовано, планувальник працює.",
            parse_mode="HTML"
        )
    else:
        logger.warning("⚠️ Telethon не авторизовано")
        await send_admin_notification(
            bot,
            "⚠️ <b>Telethon не авторизовано!</b>\n\n"
            "Перевірте STRING_SESSION в Railway Variables.",
            parse_mode="HTML"
        )
    
    try:
        await dp.start_polling(bot)
    finally:
        if is_authorized:
            await scheduler_module.scheduler.stop()
        await telegram_client.disconnect()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот зупинено")
