from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import get_interval_menu, get_back_button
from config import ADMIN_ID
from scheduler import scheduler

router = Router()

class IntervalStates(StatesGroup):
    waiting_for_custom_interval = State()

@router.callback_query(F.data == "menu_interval")
async def callback_interval_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer(" Доступ заборонено")
        return
    
    current_interval = int(await db.get_setting("interval_minutes", "60"))
    text = f" Оберіть інтервал між постами:\n\nПоточний: {format_interval(current_interval)}"
    keyboard = get_interval_menu(current_interval)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("interval_set:"))
async def callback_set_interval(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    minutes = int(callback.data.split(":")[1])
    await db.set_setting("interval_minutes", str(minutes))
    
    if scheduler:
        await scheduler.reschedule()
    
    await callback.answer(f"✅ Інтервал змінено на {format_interval(minutes)}")
    await callback_interval_menu(callback)

@router.callback_query(F.data == "interval_custom")
async def callback_custom_interval(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "✏️ Введіть інтервал в хвилинах (число):",
        reply_markup=get_back_button("menu_interval")
    )
    await state.set_state(IntervalStates.waiting_for_custom_interval)
    await callback.answer()

@router.message(IntervalStates.waiting_for_custom_interval)
async def process_custom_interval(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        minutes = int(message.text)
        if minutes < 1:
            raise ValueError
        
        await db.set_setting("interval_minutes", str(minutes))
        
        if scheduler:
            await scheduler.reschedule()
        
        await message.answer(
            f"✅ Інтервал змінено на {format_interval(minutes)}",
            reply_markup=get_back_button("menu_main")
        )
        await state.clear()
    
    except ValueError:
        await message.answer(
            " Невірний формат. Введіть число більше 0:",
            reply_markup=get_back_button("menu_interval")
        )

def format_interval(minutes: int) -> str:
    if minutes < 60:
        return f"{minutes} хв"
    elif minutes == 60:
        return "1 год"
    else:
        hours = minutes // 60
        return f"{hours} год"
