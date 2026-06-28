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
        
        # Перевіряємо чи існує файл сесії
        session_file = f"{SESSION_PATH}.session"
        logger.info(f"Шукаю файл сесії: {session_file}")
        
        if os.path.exists(session_file):
            file_size = os.path.getsize(session_file)
            logger.info(f"Файл сесії знайдено, розмір: {file_size} байт")
        else:
            logger.warning(f"Файл сесії НЕ знайдено: {session_file}")
            logger.info(f"Поточна директорія: {os.getcwd()}")
            logger.info(f"Вміст /app/data/: {os.listdir('/app/data') if os.path.exists('/app/data') else 'папка не існує'}")
        
        self.client = TelegramClient(SESSION_PATH, API_ID, API_HASH)
        
        try:
            await self.client.connect()
            
            if await self.client.is_user_authorized():
                logger.info("Telethon клієнт авторизовано")
                return True
            else:
                logger.warning("Telethon клієнт не авторизовано")
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
            logger.info(f"Код відправлено на {phone}")
            return True
        except Exception as e:
            logger.error(f"Помилка відправки коду: {e}")
            return False
    
    async def verify_code(self, code: str, phone: str, password: str = None):
        """Перевірка коду або пароля"""
        try:
            if password:
                # Двофакторна авторизація
                await self.client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=self.phone_hash,
                    password=password
                )
            else:
                # Звичайна авторизація
                await self.client.sign_in(
                    phone=phone,
                    code=code,
                    phone_code_hash=self.phone_hash
                )
            
            self.auth_pending = False
            logger.info("Telethon клієнт успішно авторизовано")
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
            
            # Завантажуємо в байти
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
