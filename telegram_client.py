import asyncio
import os
import sqlite3
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, DATABASE_PATH, ADMIN_ID
from utils import logger

class TelegramUserClient:
    def __init__(self):
        self.client = None
        self.auth_pending = False
        self.phone_hash = None
        self.phone = None
        self.bot = None
        self.session_path = None
    
    async def init(self, bot=None):
        """Ініціалізація клієнта"""
        self.bot = bot
        
        # Створюємо директорію для сесії
        session_dir = os.path.join(os.path.dirname(DATABASE_PATH), "sessions")
        os.makedirs(session_dir, exist_ok=True)
        
        self.session_path = os.path.join(session_dir, "telegram_session")
        
        logger.info(f"Шлях до сесії: {self.session_path}")
        
        self.client = TelegramClient(self.session_path, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            
            if await self.client.is_user_authorized():
                logger.info("Telethon клієнт авторизовано ✅")
                return True
            else:
                logger.warning("Telethon клієнт не авторизовано ❌")
                return False
        
        except Exception as e:
            logger.error(f"Помилка ініціалізації Telethon: {e}")
            return False
    
    async def start_auth(self, phone: str):
        """Початок авторизації"""
        try:
            result = await self.client.send_code_request(phone)
            self.phone_hash = result.phone_code_hash
            self.auth_pending = True
            self.phone = phone
            logger.info(f"Код відправлено на {phone}")
            return True
        except Exception as e:
            logger.error(f"Помилка відправки коду: {e}")
            return False
    
    async def verify_code(self, code: str, phone: str, password: str = None):
        """Перевірка коду або пароля"""
        try:
            if password:
                await self.client.sign_in(
                    phone=phone,
                    password=password
                )
            else:
                await self.client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=self.phone_hash
                )
            
            self.auth_pending = False
            logger.info("Telethon клієнт успішно авторизовано ✅")
            return True
        
        except SessionPasswordNeededError:
            logger.info("Потрібен пароль двофакторної авторизації")
            return "need_password"
        
        except Exception as e:
            logger.error(f"Помилка перевірки коду: {e}")
            return False
    
    async def get_channel_posts(self, channel, limit=None):
        """Отримання постів з каналу"""
        try:
            entity = await self.client.get_entity(channel)
            
            messages = []
            async for message in self.client.iter_messages(entity, limit=limit):
                messages.append(message)
            
            return messages
        
        except Exception as e:
            logger.error(f"Помилка отримання постів: {e}")
            return []
    
    async def get_message_by_id(self, channel, message_id):
        """Отримання конкретного поста по ID"""
        try:
            entity = await self.client.get_entity(channel)
            messages = await self.client.get_messages(entity, ids=message_id)
            
            if messages and not isinstance(messages, list):
                return messages
            elif messages and isinstance(messages, list) and messages[0]:
                return messages[0]
            
            return None
        
        except Exception as e:
            logger.error(f"Помилка отримання поста {message_id}: {e}")
            return None
    
    async def download_media(self, message):
        """Завантаження медіа в пам'ять"""
        try:
            if not message.media:
                return None
            
            media_bytes = await self.client.download_media(message, bytes)
            return media_bytes
        
        except Exception as e:
            logger.error(f"Помилка завантаження медіа: {e}")
            return None
    
    async def disconnect(self):
        """Відключення клієнта"""
        if self.client:
            await self.client.disconnect()
            logger.info("Telethon клієнт відключено")

telegram_client = TelegramUserClient()
