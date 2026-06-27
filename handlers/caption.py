from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import get_caption_menu, get_back_button
from config import ADMIN_ID

router = Router()

class CaptionStates(StatesGroup):
    waiting_for_caption = State()

@router.callback_query(F.data == "menu_caption")
async def callback_caption_menu(callback: CallbackQuery):
    """Меню підпису"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    caption = await db.get_setting("caption", "")
    has_caption = bool(caption)
    
    text = "✍️ Налаштування підпису\n\n"
    if has_caption:
        text += f"Поточний підпис:\n\"{caption}\"\n\n"
    else:
        text += "Підпис не встановлено\n\n"
    
    text += "💡 Підказка: підтримуються HTML-гіперсилки\n<a href=\"https://t.me/channel\">текст</a>"
    
    keyboard = get_caption_menu(has_caption, False)
    
    await callback.message.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "caption_edit")
async def callback_edit_caption(callback: CallbackQuery, state: FSMContext):
    """Редагування підпису"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await callback.message.edit_message_text(
        "✏️ Надішліть новий підпис:\n\n"
        "💡 Підтримуються HTML-гіперсилки:\n"
        "<a href=\"https://t.me/channel\">текст</a>",
        reply_markup=get_back_button("menu_caption"),
        parse_mode="HTML"
    )
    await state.set_state(CaptionStates.waiting_for_caption)
    await callback.answer()

@router.message(CaptionStates.waiting_for_caption)
async def process_caption(message: Message, state: FSMContext):
    """Обробка нового підпису"""
    if message.from_user.id != ADMIN_ID:
        return
    
    caption = message.text
    
    await db.set_setting("caption", caption)
    
    await message.answer(
        f"✅ Підпис збережено:\n\n\"{caption}\"",
        reply_markup=get_back_button("menu_caption"),
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "caption_remove")
async def callback_remove_caption(callback: CallbackQuery):
    """Видалення підпису"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ Доступ заборонено")
        return
    
    await db.set_setting("caption", "")
    await callback.answer("✅ Підпис видалено")
    await callback_caption_menu(callback)