import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, STRING_SESSION, ADMIN_ID
from utils import logger

class TelegramUserClient:
    def __init__(self):
        self.client = None
        self.auth_pending = False
        self.phone_hash = None
        self.phone = None
        self.bot = None
    
    async def init(self, bot=None):
        """Ініціалізація клієнта з StringSession"""
        self.bot = bot
        
        if not STRING_SESSION:
            logger.error("❌ STRING_SESSION не встановлено")
            return False
        
        logger.info(f"=== ДІАГНОСТИКА ===")
        logger.info(f"API_ID: {API_ID}")
        logger.info(f"API_HASH: {API_HASH[:10]}...")
        logger.info(f"STRING_SESSION: {STRING_SESSION[:20]}... (довжина: {len(STRING_SESSION)})")
        
        # Використовуємо StringSession замість файлу
        self.client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)
        
        try:
            await self.client.connect()
            logger.info("✅ Підключено до Telegram серверів")
            
            try:
                me = await self.client.get_me()
                logger.info(f"✅ АВТОРИЗОВАНО як @{me.username} (ID: {me.id})")
                return True
            except Exception as auth_error:
                logger.error(f"❌ Сесія невалідна: {type(auth_error).__name__}: {auth_error}")
                return False
        
        except Exception as e:
            logger.error(f"❌ Помилка підключення: {type(e).__name__}: {e}")
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
                await self.client.sign_in(phone=phone, password=password)
            else:
                await self.client.sign_in(phone=phone, code=code, phone_code_hash=self.phone_hash)
            
            self.auth_pending = False
            logger.info("✅ Telethon клієнт успішно авторизовано")
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
