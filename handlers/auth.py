from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from telethon.errors import FloodWaitError, PhoneNumberInvalidError, PhoneCodeInvalidError
from config import ADMIN_ID
from telegram_client import telegram_client
from keyboards import get_back_button
from utils import logger

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
        "🔐 <b>Авторизація Telethon</b>\n\n"
        "Надішліть номер телефону у міжнародному форматі:\n\n"
        "<b>Приклади:</b>\n"
        "🇺🇦 Україна: <code>+380501234567</code>\n"
        "🇵🇱 Польща: <code>+48123456789</code>\n"
        "🇩🇪 Німеччина: <code>+49123456789</code>\n\n"
        "⚠️ <b>Важливо:</b> використовуйте номер який прив'язаний до вашого Telegram акаунту",
        parse_mode="HTML"
    )
    await state.set_state(AuthStates.waiting_for_phone)

@router.message(AuthStates.waiting_for_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обробка номера телефону"""
    if message.from_user.id != ADMIN_ID:
        return
    
    phone = message.text.strip()
    
    # Перевірка формату
    if not phone.startswith("+"):
        await message.answer(
            "❌ Номер має починатися з +\n\n"
            "Приклад: <code>+380501234567</code>",
            parse_mode="HTML"
        )
        return
    
    status_msg = await message.answer("⏳ Підключаюсь до Telegram...")
    
    try:
        # Перевіряємо чи клієнт підключений
        if not telegram_client.client or not telegram_client.client.is_connected():
            await telegram_client.init(telegram_client.bot)
        
        await status_msg.edit_text("⏳ Відправляю код...")
        
        # Відправляємо код
        result = await telegram_client.client.send_code_request(phone)
        telegram_client.phone_hash = result.phone_code_hash
        telegram_client.auth_pending = True
        telegram_client.phone = phone
        
        logger.info(f"Код відправлено на {phone}")
        
        await status_msg.edit_text(
            f"✅ <b>Код відправлено!</b>\n\n"
            f"📱 Номер: <code>{phone}</code>\n\n"
            f"🔍 <b>Де шукати код:</b>\n"
            f"1. Відкрий Telegram на телефоні\n"
            f"2. Знайди чат <b>\"Telegram\"</b> (синя іконка, верифікований)\n"
            f"3. Там буде 5-значний код\n\n"
            f"⚠️ <b>НЕ шукай в SMS</b> — код приходить в Telegram додаток!\n\n"
            f"Надішліть код:",
            parse_mode="HTML"
        )
        await state.set_state(AuthStates.waiting_for_code)
    
    except PhoneNumberInvalidError:
        await status_msg.edit_text(
            "❌ <b>Невірний номер телефону</b>\n\n"
            "Перевірте формат і спробуйте ще раз:",
            parse_mode="HTML"
        )
    
    except FloodWaitError as e:
        await status_msg.edit_text(
            f"⚠️ <b>Забагато спроб</b>\n\n"
            f"Зачекайте {e.seconds} секунд і спробуйте ще раз",
            parse_mode="HTML"
        )
    
    except Exception as e:
        logger.error(f"Помилка відправки коду: {e}")
        await status_msg.edit_text(
            f"❌ <b>Помилка відправки коду</b>\n\n"
            f"Причина: {e}\n\n"
            f"Спробуйте ще раз:",
            parse_mode="HTML"
        )

@router.message(AuthStates.waiting_for_code)
async def process_code(message: Message, state: FSMContext):
    """Обробка коду"""
    if message.from_user.id != ADMIN_ID:
        return
    
    code = message.text.strip().replace(" ", "")
    
    # Перевірка формату
    if not code.isdigit() or len(code) != 5:
        await message.answer(
            "❌ Код має бути 5 цифр\n\n"
            "Спробуйте ще раз:",
            parse_mode="HTML"
        )
        return
    
    status_msg = await message.answer("⏳ Перевіряю код...")
    
    try:
        phone = telegram_client.phone
        
        await telegram_client.client.sign_in(
            phone=phone,
            code=code,
            phone_code_hash=telegram_client.phone_hash
        )
        
        telegram_client.auth_pending = False
        
        await status_msg.edit_text(
            "✅ <b>Авторизація успішна!</b>\n\n"
            "🎉 Тепер бот може читати пости з каналу-джерела.\n\n"
            "Бот автоматично перезапуститься через 5 секунд...",
            parse_mode="HTML"
        )
        
        await state.clear()
        
        # Перезапускаємо планувальник
        import asyncio
        from scheduler import scheduler
        
        if scheduler:
            await asyncio.sleep(5)
            await scheduler.start()
            await message.answer("✅ Бот запущено!")
    
    except PhoneCodeInvalidError:
        await status_msg.edit_text(
            "❌ <b>Невірний код</b>\n\n"
            "Спробуйте ще раз:",
            parse_mode="HTML"
        )
    
    except Exception as e:
        # Можливо потрібен пароль
        from telethon.errors import SessionPasswordNeededError
        
        if isinstance(e, SessionPasswordNeededError):
            await status_msg.edit_text(
                "🔐 <b>Потрібен пароль двофакторної авторизації</b>\n\n"
                "Надішліть пароль:",
                parse_mode="HTML"
            )
            await state.set_state(AuthStates.waiting_for_password)
        else:
            logger.error(f"Помилка перевірки коду: {e}")
            await status_msg.edit_text(
                f"❌ <b>Помилка</b>\n\n"
                f"Причина: {e}\n\n"
                f"Спробуйте ще раз:",
                parse_mode="HTML"
            )

@router.message(AuthStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    """Обробка пароля 2FA"""
    if message.from_user.id != ADMIN_ID:
        return
    
    password = message.text.strip()
    
    status_msg = await message.answer("⏳ Перевіряю пароль...")
    
    try:
        phone = telegram_client.phone
        
        await telegram_client.client.sign_in(
            phone=phone,
            password=password
        )
        
        telegram_client.auth_pending = False
        
        await status_msg.edit_text(
            "✅ <b>Авторизація успішна!</b>\n\n"
            "🎉 Тепер бот може читати пости з каналу-джерела.",
            parse_mode="HTML"
        )
        
        await state.clear()
        
        # Перезапускаємо планувальник
        import asyncio
        from scheduler import scheduler
        
        if scheduler:
            await asyncio.sleep(5)
            await scheduler.start()
            await message.answer("✅ Бот запущено!")
    
    except Exception as e:
        logger.error(f"Помилка перевірки пароля: {e}")
        await status_msg.edit_text(
            f"❌ <b>Невірний пароль</b>\n\n"
            f"Спробуйте ще раз:",
            parse_mode="HTML"
        )
