import time
from datetime import datetime
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db
from keyboards import get_back_button
from config import ADMIN_ID
from scheduler import scheduler
from utils import format_datetime

router = Router()

@router.callback_query(F.data == "action_toggle")
async def callback_toggle(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    current = await db.get_setting("is_running", "1")
    new_value = "0" if current == "1" else "1"
    await db.set_setting("is_running", new_value)
    
    if scheduler:
        await scheduler.reschedule()
    
    status = "▶️ Працює" if new_value == "1" else "⏸ Пауза"
    await callback.answer(f"Статус: {status}")
    
    from .start import callback_main_menu
    await callback_main_menu(callback)

@router.callback_query(F.data == "action_publish_now")
async def callback_publish_now(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(" Доступ заборонено")
        return
    
    await callback.answer("⏳ Публікація...")
    
    if scheduler:
        await scheduler.publish_now()
        await callback.answer("✅ Пост опубліковано")
    else:
        await callback.answer("❌ Планувальник не ініціалізовано")

@router.callback_query(F.data == "action_ping")
async def callback_ping(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    start_time = time.time()
    await callback.answer()
    end_time = time.time()
    latency = int((end_time - start_time) * 1000)
    
    now = datetime.now()
    time_str = format_datetime(now)
    
    text = (
        f"🏓 Pong!\n\n"
        f"✅ Бот працює\n"
        f"⚡ Затримка: {latency} мс\n"
        f"🕐 Час сервера: {time_str}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_back_button())

@router.callback_query(F.data == "menu_stats")
async def callback_stats(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    published_count = await db.get_published_count()
    last_published = await db.get_last_published_time()
    
    mode = await db.get_setting("mode", "randomsmart")
    mode_names = {
        "sequential": "🔢 Послідовно",
        "random": "🎲 Випадково",
        "randomsmart": "🧠 RandomSmart"
    }
    
    smart_n = await db.get_setting("smart_n", "100")
    interval = await db.get_setting("interval_minutes", "60")
    caption = await db.get_setting("caption", "")
    
    text = (
        f"📊 Детальна статистика\n\n"
        f"✅ Вже опубліковано: {published_count}\n"
    )
    
    if last_published:
        text += f"🕐 Останній пост: {format_datetime(last_published)}\n"
    else:
        text += f"🕐 Останній пост: ще не публікувалось\n"
    
    text += (
        f"\n"
        f"🎛 Режим: {mode_names.get(mode, mode)}\n"
    )
    
    if mode == "randomsmart":
        text += f"🧠 N для RandomSmart: {smart_n}\n"
    
    text += f"⏱ Інтервал: {interval} хв\n"
    text += f"️ Підпис: {'[встановлено]' if caption else '[не встановлено]'}"
    
    await callback.message.edit_text(text, reply_markup=get_back_button())
    await callback.answer()
