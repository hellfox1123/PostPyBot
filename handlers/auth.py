from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_ID
from telegram_client import telegram_client
from keyboards import get_back_button

router = Router()

class AuthStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_code = State()
    waiting_for_password = State()

@router.message(Command("auth"))
async def cmd_auth(message: Message, state: FSMContext):
    """Команда для авторизації Telethon"""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Доступ заборонено")
        return
    
    # Перевіряємо чи вже авторизовано
    if telegram_client.client and await telegram_client.client.is_user_authorized():
        await message.answer("✅ Telethon вже авторизовано")
        return
    
    await message.answer(
        "🔐 Авторизація Telethon\n\n"
        "Надішліть номер телефону у міжнародному форматі:\n"
        "Приклад: +380501234567",
        reply_markup=get_back_button()
    )
    await state.set_state(AuthStates.waiting_for_phone)

@router.message(AuthStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обробка номера телефону"""
    if message.from_user.id != ADMIN_ID:
        return
    
    phone = message.text.strip()
    
    await message.answer("⏳ Відправляю код...")
    
    success = await telegram_client.start_auth(phone)
    
    if success:
        await state.update_data(phone=phone)
        await message.answer(
            "✅ Код відправлено!\n\n"
            "Надішліть код з Telegram:",
            reply_markup=get_back_button()
        )
        await state.set_state(AuthStates.waiting_for_code)
    else:
        await message.answer(
            "❌ Помилка відправки коду. Перевірте номер і спробуйте ще раз:",
            reply_markup=get_back_button()
        )

@router.message(AuthStates.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    """Обробка коду"""
    if message.from_user.id != ADMIN_ID:
        return
    
    code = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")
    
    await message.answer("⏳ Перевіряю код...")
    
    result = await telegram_client.verify_code(code, phone)
    
    if result is True:
        await message.answer(
            "✅ Авторизація успішна!\n\n"
            "Тепер бот може читати пости з каналу-джерела."
        )
        await state.clear()
    elif result == "need_password":
        await message.answer(
            "🔐 Потрібен пароль двофакторної авторизації:\n\n"
            "Надішліть пароль:",
            reply_markup=get_back_button()
        )
        await state.set_state(AuthStates.waiting_for_password)
    else:
        await message.answer(
            "❌ Невірний код. Спробуйте ще раз:",
            reply_markup=get_back_button()
        )

@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    """Обробка пароля"""
    if message.from_user.id != ADMIN_ID:
        return
    
    password = message.text.strip()
    data = await state.get_data()
    phone = data.get("phone")
    
    await message.answer("⏳ Перевіряю пароль...")
    
    result = await telegram_client.verify_code("", phone, password)
    
    if result is True:
        await message.answer(
            "✅ Авторизація успішна!\n\n"
            "Тепер бот може читати пости з каналу-джерела."
        )
        await state.clear()
    else:
        await message.answer(
            "❌ Невірний пароль. Спробуйте ще раз:",
            reply_markup=get_back_button()
        )