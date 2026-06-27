from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import get_mode_menu, get_smart_n_menu, get_back_button
from config import ADMIN_ID

router = Router()

class SmartNStates(StatesGroup):
    waiting_for_smart_n = State()

@router.callback_query(F.data == "menu_mode")
async def callback_mode_menu(callback: CallbackQuery):
    """Меню режиму"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    current_mode = await db.get_setting("mode", "randomsmart")
    text = f"🎛 Оберіть режим постингу:\n\nПоточний: {get_mode_name(current_mode)}"
    keyboard = get_mode_menu(current_mode)
    
    await callback.message.edit_message_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("mode_set:"))
async def callback_set_mode(callback: CallbackQuery):
    """Встановлення режиму"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    mode = callback.data.split(":")[1]
    await db.set_setting("mode", mode)
    
    await callback.answer(f"✅ Режим змінено на {get_mode_name(mode)}")
    await callback_mode_menu(callback)

@router.callback_query(F.data == "mode_smart_settings")
async def callback_smart_settings(callback: CallbackQuery):
    """Налаштування RandomSmart"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    current_n = int(await db.get_setting("smart_n", "100"))
    text = f"🧠 RandomSmart налаштування\n\nКількість останніх постів, які не повторюватимуться:\nПоточне значення: {current_n}"
    keyboard = get_smart_n_menu(current_n)
    
    await callback.message.edit_message_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data.startswith("smart_n:"))
async def callback_set_smart_n(callback: CallbackQuery):
    """Встановлення N для RandomSmart"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    n = int(callback.data.split(":")[1])
    await db.set_setting("smart_n", str(n))
    
    await callback.answer(f"✅ N змінено на {n}")
    await callback_smart_settings(callback)

@router.callback_query(F.data == "smart_n_custom")
async def callback_custom_smart_n(callback: CallbackQuery, state: FSMContext):
    """Введення свого N"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_message_text(
        "✏️ Введіть число (кількість постів):",
        reply_markup=get_back_button("mode_smart_settings")
    )
    await state.set_state(SmartNStates.waiting_for_smart_n)
    await callback.answer()

@router.message(SmartNStates.waiting_for_smart_n)
async def process_smart_n(message: Message, state: FSMContext):
    """Обробка введеного N"""
    if message.from_user.id != ADMIN_ID:
        return
    
    try:
        n = int(message.text)
        if n < 1:
            raise ValueError
        
        await db.set_setting("smart_n", str(n))
        
        await message.answer(
            f"✅ N змінено на {n}",
            reply_markup=get_back_button("menu_mode")
        )
        await state.clear()
    
    except ValueError:
        await message.answer(
            "❌ Невірний формат. Введіть число більше 0:",
            reply_markup=get_back_button("mode_smart_settings")
        )

def get_mode_name(mode: str) -> str:
    """Назва режиму"""
    names = {
        "sequential": "🔢 Послідовно",
        "random": "🎲 Випадково",
        "randomsmart": "🧠 RandomSmart"
    }
    return names.get(mode, mode)