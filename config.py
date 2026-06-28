import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram API - ТВОЇ КЛЮЧІ з my.telegram.org
API_ID = 20145164  # ← твій api_id
API_HASH = 'cb587ee5271bde0c92bb783b23eafa99'  # ← твій api_hash

# IDs
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL", "")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "xposter.db")

# Session
SESSION_PATH = os.getenv("SESSION_PATH", "data/telegram_session")

# Defaults
DEFAULT_INTERVAL_MINUTES = int(os.getenv("DEFAULT_INTERVAL_MINUTES", "60"))
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "randomsmart")
DEFAULT_SMART_N = int(os.getenv("DEFAULT_SMART_N", "100"))

# Перевірка
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не встановлено в .env")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не встановлено в .env")
if not SOURCE_CHANNEL:
    raise ValueError("SOURCE_CHANNEL не встановлено в .env")
if not TARGET_CHANNEL_ID:
    raise ValueError("TARGET_CHANNEL_ID не встановлено в .env")
