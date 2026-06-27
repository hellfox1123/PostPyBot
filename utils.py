import logging
from datetime import datetime
from aiogram import Bot
from config import ADMIN_ID

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def send_admin_notification(bot: Bot, message: str):
    """Надіслати сповіщення адміну"""
    try:
        await bot.send_message(ADMIN_ID, message)
    except Exception as e:
        logger.error(f"Помилка відправки сповіщення адміну: {e}")

def format_datetime(dt: datetime) -> str:
    """Форматування дати/часу"""
    return dt.strftime("%d.%m.%Y %H:%M:%S")

def has_blur_marker(text: str) -> bool:
    """Перевірка наявності маркера блюру"""
    if not text:
        return False
    blur_words = ["блюр", "blur"]
    text_lower = text.lower()
    return any(word in text_lower for word in blur_words)