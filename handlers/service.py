import os
from aiogram import Router, F
from aiogram.types import CallbackQuery, FSInputFile
from database import db
from keyboards import get_service_menu, get_confirm_keyboard, get_back_button
from config import ADMIN_ID, DATABASE_PATH
from utils import logger

router = Router()

@router.callback_query(F.data == "menu_service")
async def callback_service_menu(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    test_mode = await db.get_setting("test_mode", "0") == "1"
    text = "🛠 Сервісні налаштування\n\n"
    text += "💡 Тестовий режим: пости надходитимуть тобі в приватні повідомлення замість цільового каналу."
    
    keyboard = get_service_menu(test_mode)
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()

@router.callback_query(F.data == "service_toggle_test")
async def callback_toggle_test(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    current = await db.get_setting("test_mode", "0")
    new_value = "0" if current == "1" else "1"
    await db.set_setting("test_mode", new_value)
    
    status = "✅ Увімкнено" if new_value == "1" else "❌ Вимкнено"
    await callback.answer(f"Тестовий режим: {status}")
    await callback_service_menu(callback)

@router.callback_query(F.data == "service_export")
async def callback_export(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    try:
        if os.path.exists(DATABASE_PATH):
            file = FSInputFile(DATABASE_PATH)
            await callback.message.answer_document(file, caption="📤 Експорт бази даних")
            await callback.answer("✅ База експортована")
        else:
            await callback.answer("❌ База даних не знайдена")
    except Exception as e:
        logger.error(f"Помилка експорту: {e}")
        await callback.answer(f"❌ Помилка: {e}")

@router.callback_query(F.data == "service_import")
async def callback_import(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "📥 Надішліть файл бази даних (.db)",
        reply_markup=get_back_button("menu_service")
    )
    await callback.answer()

@router.callback_query(F.data == "service_clear")
async def callback_clear(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_text(
        "⚠️ Ви впевнені що хочете очистити всю історію опублікованих постів?\n\n"
        "Це не можна скасувати!",
        reply_markup=get_confirm_keyboard("clear_history")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("confirm_yes:"))
async def callback_confirm_yes(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    action = callback.data.split(":")[1]
    
    if action == "clear_history":
        await db.clear_all_data()
        await callback.message.edit_text(
            "✅ Історію очищено",
            reply_markup=get_back_button("menu_service")
        )
    
    await callback.answer("✅ Виконано")

@router.callback_query(F.data.startswith("confirm_no:"))
async def callback_confirm_no(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback_service_menu(callback)
    await callback.answer("❌ Скасовано")

@router.callback_query(F.data == "service_logs")
async def callback_logs(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    try:
        log_path = "/app/data/bot.log"
        if os.path.exists(log_path):
            file = FSInputFile(log_path)
            await callback.message.answer_document(file, caption=" Логи бота")
            await callback.answer("✅ Логи надіслано")
        else:
            await callback.answer("❌ Файл логів не знайдено")
    except Exception as e:
        logger.error(f"Помилка надсилання логів: {e}")
        await callback.answer(f"❌ Помилка: {e}")
