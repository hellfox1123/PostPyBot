from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from database import db
from keyboards import get_main_menu
from config import ADMIN_ID

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ заборонено")
        return
    await show_main_menu(message)

@router.callback_query(F.data == "menu_main")
async def callback_main_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    await show_main_menu(callback)

async def show_main_menu(target):
    """
    target може бути Message або CallbackQuery
    """
    is_running = await db.get_setting("is_running", "1") == "1"
    test_mode = await db.get_setting("test_mode", "0") == "1"
    
    mode = await db.get_setting("mode", "randomsmart")
    mode_names = {
        "sequential": "🔢 Послідовно",
        "random": "🎲 Випадково",
        "randomsmart": "🧠 RandomSmart"
    }
    
    interval = await db.get_setting("interval_minutes", "60")
    interval_text = format_interval(int(interval))
    
    caption = await db.get_setting("caption", "")
    caption_text = "[встановлено]" if caption else "[не встановлено]"
    
    published_count = await db.get_published_count()
    
    text = (
        f" XPoster Bot\n\n"
        f"📊 Статус: {'▶️ Працює' if is_running else '⏸ Пауза'}\n"
        f" Режим: {mode_names.get(mode, mode)}\n"
        f"⏱ Інтервал: {interval_text}\n"
        f"️ Підпис: {caption_text}\n\n"
        f"📈 Опубліковано: {published_count}"
    )
    
    keyboard = get_main_menu(is_running, test_mode)
    
    # Розрізняємо Message і CallbackQuery
    if isinstance(target, CallbackQuery):
        await target.message.edit_text(text, reply_markup=keyboard)
        await target.answer()
    else:
        # Це Message
        await target.answer(text, reply_markup=keyboard)

def format_interval(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} хв"
    elif minutes == 60:
        return "1 год"
    else:
        hours = minutes // 60
        return f"{hours} год"
