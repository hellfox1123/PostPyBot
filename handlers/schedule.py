from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import get_back_button
from config import ADMIN_ID

router = Router()

class ScheduleStates(StatesGroup):
    waiting_for_hours = State()
    waiting_for_days = State()

@router.callback_query(F.data == "menu_schedule")
async def callback_schedule_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    start_hour = await db.get_setting("schedule_hours_start", "0")
    end_hour = await db.get_setting("schedule_hours_end", "24")
    days = await db.get_setting("schedule_days", "1,2,3,4,5,6,7")
    
    day_names = {
        "1": "Пн", "2": "Вт", "3": "Ср", "4": "Чт",
        "5": "Пт", "6": "Сб", "7": "Нд"
    }
    
    active_days = [day_names[d] for d in days.split(",") if d in day_names]
    
    if end_hour == "24":
        time_text = "Цілодобово"
    else:
        time_text = f"{start_hour}:00 - {end_hour}:00"
    
    text = (
        f"📅 Розклад постингу\n\n"
        f"🕐 Години активності: {time_text}\n"
        f"📋 Дні тижня: {', '.join(active_days)}\n\n"
        f"Оберіть що змінити:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🕐 Змінити години", callback_data="schedule_hours")],
        [InlineKeyboardButton(text="📋 Змінити дні", callback_data="schedule_days")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "schedule_hours")
async def callback_schedule_hours(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "✏️ Введіть години активності у форматі:\n"
        "початок-кінець\n\n"
        "Приклади:\n"
        "9-23 (з 9:00 до 23:00)\n"
        "0-24 (цілодобово)\n"
        "10-22 (з 10:00 до 22:00)",
        reply_markup=get_back_button("menu_schedule")
    )
    await state.set_state(ScheduleStates.waiting_for_hours)
    await callback.answer()

@router.message(ScheduleStates.waiting_for_hours)
async def process_schedule_hours(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        text = message.text.strip()
        start, end = text.split("-")
        start_hour = int(start)
        end_hour = int(end)
        
        if not (0 <= start_hour <= 23 and 0 <= end_hour <= 24):
            raise ValueError
        
        await db.set_setting("schedule_hours_start", str(start_hour))
        await db.set_setting("schedule_hours_end", str(end_hour))
        
        await message.answer(
            f"✅ Години змінено: {start_hour}:00 - {end_hour}:00",
            reply_markup=get_back_button("menu_schedule")
        )
        await state.clear()
    
    except Exception:
        await message.answer(
            "❌ Невірний формат. Приклад: 9-23",
            reply_markup=get_back_button("menu_schedule")
        )

@router.callback_query(F.data == "schedule_days")
async def callback_schedule_days(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "✏️ Введіть дні тижня через кому:\n\n"
        "1 = Понеділок\n"
        "2 = Вівторок\n"
        "3 = Середа\n"
        "4 = Четвер\n"
        "5 = П'ятниця\n"
        "6 = Субота\n"
        "7 = Неділя\n\n"
        "Приклади:\n"
        "1,2,3,4,5 (будні)\n"
        "6,7 (вихідні)\n"
        "1,2,3,4,5,6,7 (усі дні)",
        reply_markup=get_back_button("menu_schedule")
    )
    await state.set_state(ScheduleStates.waiting_for_days)
    await callback.answer()

@router.message(ScheduleStates.waiting_for_days)
async def process_schedule_days(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        days = message.text.strip().replace(" ", "")
        day_list = [int(d) for d in days.split(",")]
        
        if not all(1 <= d <= 7 for d in day_list):
            raise ValueError
        
        await db.set_setting("schedule_days", days)
        
        await message.answer(
            f"✅ Дні змінено: {days}",
            reply_markup=get_back_button("menu_schedule")
        )
        await state.clear()
    
    except Exception:
        await message.answer(
            "❌ Невірний формат. Приклад: 1,2,3,4,5",
            reply_markup=get_back_button("menu_schedule")
        )
