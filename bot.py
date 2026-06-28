import asyncio
import logging
import os
import base64
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


def restore_session_from_variables():
    """Відновлення сесії з Railway Variables (розбита на частини)"""
    # Збираємо сесію з кількох змінних SESSION_DATA_1, SESSION_DATA_2, ...
    session_chunks = []
    i = 1
    while True:
        chunk = os.getenv(f"SESSION_DATA_{i}", "")
        if not chunk:
            break
        session_chunks.append(chunk)
        i += 1
    
    if not session_chunks:
        logger.warning("⚠️ SESSION_DATA змінні не знайдено в Railway Variables")
        return False
    
    try:
        session_base64 = "".join(session_chunks)
        session_bytes = base64.b64decode(session_base64)
        
        # Шлях до файлу сесії
        session_dir = os.path.dirname(DATABASE_PATH)
        session_file = os.path.join(session_dir, "telegram_session.session")
        os.makedirs(session_dir, exist_ok=True)
        
        # Перевіряємо чи файл вже актуальний
        if os.path.exists(session_file):
            with open(session_file, 'rb') as f:
                existing_data = f.read()
            if existing_data == session_bytes:
                logger.info("✅ Сесія вже актуальна (не треба оновлювати)")
                return True
        
        # Зберігаємо нову сесію
        with open(session_file, 'wb') as f:
            f.write(session_bytes)
        
        logger.info(f"✅ Сесію відновлено з Railway Variables ({len(session_bytes)} байт)")
        return True
    
    except Exception as e:
        logger.error(f"❌ Помилка відновлення сесії: {e}")
        return False


async def main():
    """Головна функція"""
    
    # Створюємо директорію для бази якщо її немає
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    # Відновлюємо сесію з Railway Variables
    logger.info("=== ВІДНОВЛЕННЯ СЕСІЇ ===")
    session_restored = restore_session_from_variables()
    
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
            "Сесія невалідна або відсутня.\n\n"
            "Перевірте SESSION_DATA в Railway Variables.",
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
