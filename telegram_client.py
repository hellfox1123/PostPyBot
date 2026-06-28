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
        
        # Використовуємо файл з GitHub
        session_file = f"{SESSION_PATH}.session"
        logger.info(f"Шукаю файл сесії: {session_file}")
        
        if os.path.exists(session_file):
            file_size = os.path.getsize(session_file)
            logger.info(f"✅ Файл сесії знайдено, розмір: {file_size} байт")
        else:
            logger.warning(f"❌ Файл сесії НЕ знайдено: {session_file}")
            logger.info(f"Поточна директорія: {os.getcwd()}")
        
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
