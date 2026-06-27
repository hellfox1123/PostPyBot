import aiosqlite
from config import DATABASE_PATH
from datetime import datetime
from typing import List, Optional

class Database:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    async def init(self):
        """Ініціалізація бази даних"""
        async with aiosqlite.connect(self.db_path) as db:
            # Таблиця опублікованих постів
            await db.execute("""
                CREATE TABLE IF NOT EXISTS published_posts (
                    post_id INTEGER PRIMARY KEY,
                    published_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    target_message_id INTEGER
                )
            """)
            
            # Таблиця налаштувань
            await db.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            
            # Таблиця мульти-підписів
            await db.execute("""
                CREATE TABLE IF NOT EXISTS captions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    caption_text TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Таблиця кнопок під постами
            await db.execute("""
                CREATE TABLE IF NOT EXISTS post_buttons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    button_text TEXT,
                    button_url TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            await db.commit()
            
            # Ініціалізація дефолтних налаштувань
            await self._init_defaults(db)
    
    async def _init_defaults(self, db):
        """Встановлення дефолтних налаштувань якщо їх немає"""
        defaults = {
            "interval_minutes": "60",
            "mode": "randomsmart",
            "smart_n": "100",
            "is_running": "1",
            "test_mode": "0",
            "caption": "",
            "schedule_hours_start": "0",
            "schedule_hours_end": "24",
            "schedule_days": "1,2,3,4,5,6,7"
        }
        
        for key, value in defaults.items():
            cursor = await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
        
        await db.commit()
    
    async def get_setting(self, key: str, default: str = "") -> str:
        """Отримання налаштування"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            )
            row = await cursor.fetchone()
            return row[0] if row else default
    
    async def set_setting(self, key: str, value: str):
        """Збереження налаштування"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )
            await db.commit()
    
    async def add_published_post(self, post_id: int, target_message_id: int):
        """Додати опублікований пост"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO published_posts (post_id, target_message_id) VALUES (?, ?)",
                (post_id, target_message_id)
            )
            await db.commit()
    
    async def get_published_post_ids(self, limit: Optional[int] = None) -> List[int]:
        """Отримати список ID опублікованих постів"""
        async with aiosqlite.connect(self.db_path) as db:
            query = "SELECT post_id FROM published_posts ORDER BY published_at DESC"
            if limit:
                query += f" LIMIT {limit}"
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def get_published_count(self) -> int:
        """Кількість опублікованих постів"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM published_posts")
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    async def get_last_published_time(self) -> Optional[datetime]:
        """Час останньої публікації"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT published_at FROM published_posts ORDER BY published_at DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            if row:
                return datetime.fromisoformat(row[0])
            return None
    
    async def get_all_captions(self) -> List[str]:
        """Отримати всі активні мульти-підписи"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT caption_text FROM captions WHERE is_active = 1"
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
    
    async def add_caption(self, caption_text: str):
        """Додати мульти-підпис"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO captions (caption_text) VALUES (?)",
                (caption_text,)
            )
            await db.commit()
    
    async def clear_captions(self):
        """Очистити всі мульти-підписи"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM captions")
            await db.commit()
    
    async def get_all_buttons(self) -> List[tuple]:
        """Отримати всі активні кнопки"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT button_text, button_url FROM post_buttons WHERE is_active = 1"
            )
            rows = await cursor.fetchall()
            return rows
    
    async def add_button(self, text: str, url: str):
        """Додати кнопку"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO post_buttons (button_text, button_url) VALUES (?, ?)",
                (text, url)
            )
            await db.commit()
    
    async def clear_buttons(self):
        """Очистити всі кнопки"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM post_buttons")
            await db.commit()
    
    async def clear_all_data(self):
        """Очистити всю історію"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM published_posts")
            await db.commit()

db = Database()