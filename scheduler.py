import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database import db
import poster as poster_module  # <-- Імпортуємо весь модуль
from utils import logger, send_admin_notification
from aiogram import Bot

class Scheduler:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.job = None
    
    async def start(self):
        """Запуск планувальника"""
        self.scheduler.start()
        await self._reschedule_job()
        logger.info("Планувальник запущено")
    
    async def stop(self):
        """Зупинка планувальника"""
        if self.job:
            self.job.remove()
            self.job = None
        self.scheduler.shutdown()
        logger.info("Планувальник зупинено")
    
    async def _reschedule_job(self):
        """Переналаштування завдання"""
        if self.job:
            self.job.remove()
            self.job = None
        
        is_running = await db.get_setting("is_running", "1") == "1"
        if not is_running:
            logger.info("Бот на паузі, завдання не створено")
            return
        
        interval_minutes = int(await db.get_setting("interval_minutes", "60"))
        
        self.job = self.scheduler.add_job(
            self._publish_post,
            IntervalTrigger(minutes=interval_minutes),
            id="publish_post",
            name="Автоматична публікація поста",
            replace_existing=True
        )
        
        logger.info(f"Завдання створено: інтервал {interval_minutes} хв")
    
    async def _publish_post(self):
        """Публікація поста"""
        try:
            # Перевіряємо чи poster ініціалізовано
            if not poster_module.poster:
                logger.error("❌ Poster не ініціалізовано!")
                return

            if not await self._is_in_schedule():
                logger.info("Поза робочим часом, пропуск")
                return
            
            # ВИПРАВЛЕНО: звертаємось до poster через модуль
            post_id = await poster_module.poster.get_next_post()
            
            if not post_id:
                await send_admin_notification(
                    self.bot,
                    "⚠️ Всі пости з каналу-джерела опубліковано!\n\n"
                    "Додайте нові пости або скиньте історію через меню Сервіс."
                )
                return
            
            # ВИПРАВЛЕНО: звертаємось до poster через модуль
            success = await poster_module.poster.copy_post(post_id)
            
            if success:
                logger.info(f"✅ Пост {post_id} успішно опубліковано")
            else:
                logger.warning(f"⚠️ Пост {post_id} не вдалося опублікувати")
        
        except Exception as e:
            logger.error(f"❌ Критична помилка при публікації: {e}")
            await send_admin_notification(
                self.bot,
                f"❌ Критична помилка планувальника\n\n{e}"
            )
    
    async def _is_in_schedule(self) -> bool:
        """Перевірка чи зараз робочий час"""
        now = datetime.now()
        
        schedule_days = await db.get_setting("schedule_days", "1,2,3,4,5,6,7")
        days = [int(d) for d in schedule_days.split(",")]
        current_day = now.isoweekday()
        
        if current_day not in days:
            return False
        
        start_hour = int(await db.get_setting("schedule_hours_start", "0"))
        end_hour = int(await db.get_setting("schedule_hours_end", "24"))
        current_hour = now.hour
        
        if end_hour == 24:
            return True
        else:
            return start_hour <= current_hour < end_hour
    
    async def publish_now(self):
        """Негайна публікація (вручну)"""
        await self._publish_post()
    
    async def reschedule(self):
        """Публічний метод для переналаштування"""
        await self._reschedule_job()

scheduler = None
