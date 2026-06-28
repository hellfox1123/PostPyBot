import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Telegram API
API_ID = 20145164
API_HASH = 'cb587ee5271bde0c92bb783b23eafa99'

# IDs
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SOURCE_CHANNEL = os.getenv("SOURCE_CHANNEL", "")
TARGET_CHANNEL_ID = int(os.getenv("TARGET_CHANNEL_ID", "0"))

# Database
DATABASE_PATH = os.getenv("DATABASE_PATH", "xposter.db")

# String Session (з Railway Variables)
STRING_SESSION = os.getenv("STRING_SESSION", "")

# Defaults
DEFAULT_INTERVAL_MINUTES = int(os.getenv("DEFAULT_INTERVAL_MINUTES", "60"))
DEFAULT_MODE = os.getenv("DEFAULT_MODE", "randomsmart")
DEFAULT_SMART_N = int(os.getenv("DEFAULT_SMART_N", "100"))

# Перевірка
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не встановлено")
if not ADMIN_ID:
    raise ValueError("ADMIN_ID не встановлено")
if not SOURCE_CHANNEL:
    raise ValueError("SOURCE_CHANNEL не встановлено")
if not TARGET_CHANNEL_ID:
    raise ValueError("TARGET_CHANNEL_ID не встановлено")
if not STRING_SESSION:
    raise ValueError("STRING_SESSION не встановлено")
