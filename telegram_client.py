import asyncio
import os
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, SESSION_PATH, ADMIN_ID
from utils import logger

class TelegramUserClient:
    def __init__(self):
        self.client = None
        self.auth_pending = False
        self.phone_hash = None
        self.phone = None
        self.bot = None
    
    async def init(self, bot=None):
        """Ініціалізація клієнта"""
        self.bot = bot
        
        # Детальне логування
        logger.info(f"=== ДІАГНОСТИКА ФАЙЛУ СЕСІЇ ===")
        logger.info(f"SESSION_PATH з config: {SESSION_PATH}")
        logger.info(f"Поточна робоча директорія: {os.getcwd()}")
        
        # Перевіряємо різні можливі шляхи
        possible_paths = [
            f"{SESSION_PATH}.session",
            f"/app/{SESSION_PATH}.session",
            f"/app/data/telegram_session.session",
            "data/telegram_session.session",
            "telegram_session.session"
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                file_size = os.path.getsize(path)
                logger.info(f"✅ ФАЙЛ ЗНАЙДЕНО: {path} ({file_size} байт)")
            else:
                logger.info(f"❌ Не знайдено: {path}")
        
        # Перевіряємо вміст /app/data/
        if os.path.exists("/app/data"):
            logger.info(f"Вміст /app/data/: {os.listdir('/app/data')}")
        else:
            logger.warning("Папка /app/data/ не існує")
        
        # Перевіряємо /app/
        if os.path.exists("/app"):
            logger.info(f"Вміст /app/: {os.listdir('/app')}")
        
        # Використовуємо SESSION_PATH
        session_file = f"{SESSION_PATH}.session"
        logger.info(f"Використовую шлях: {session_file}")
        
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            
            if await self.client.is_user_authorized():
                logger.info("✅ Telethon клієнт авторизовано")
                return True
            else:
                logger.warning("❌ Telethon клієнт не авторизовано")
                return False
        
        except Exception as e:
            logger.error(f"Помилка ініціалізації Telethon: {e}")
            return False
    
    # ... решта методів без змін ...

telegram_client = TelegramUserClient()
