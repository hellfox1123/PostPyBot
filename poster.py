import asyncio
import random
import io
from typing import Optional, List
from aiogram import Bot
from aiogram.types import (
    InputMediaPhoto, InputMediaVideo, InputMediaAnimation,
    InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
)
from aiogram.exceptions import TelegramRetryAfter, TelegramBadRequest
from database import db
from config import SOURCE_CHANNEL, TARGET_CHANNEL_ID, ADMIN_ID
from telegram_client import telegram_client
from utils import logger, send_admin_notification, has_blur_marker

class Poster:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.retry_attempts = 3
        self.retry_delays = [5, 15, 30]
    
    async def get_all_post_ids(self) -> List[int]:
        """Отримання всіх ID постів з каналу-джерела"""
        try:
            messages = await telegram_client.get_channel_posts(SOURCE_CHANNEL)
            post_ids = [msg.id for msg in messages if msg.media]  # Тільки з медіа
            logger.info(f"Знайдено {len(post_ids)} постів з медіа в каналі-джерелі")
            return post_ids
        except Exception as e:
            logger.error(f"Помилка отримання списку постів: {e}")
            return []
    
    async def get_next_post(self) -> Optional[int]:
        """Вибір наступного поста для публікації"""
        mode = await db.get_setting("mode", "randomsmart")
        
        # Отримуємо всі пости з джерела
        all_post_ids = await self.get_all_post_ids()
        if not all_post_ids:
            return None
        
        # Отримуємо вже опубліковані
        published_ids = await db.get_published_post_ids()
        available_posts = [pid for pid in all_post_ids if pid not in published_ids]
        
        if not available_posts:
            logger.info("Всі пости вже опубліковані")
            return None
        
        # Вибір згідно з режимом
        if mode == "sequential":
            # Найстаріший (найменший ID)
            return min(available_posts)
        
        elif mode == "random":
            # Повністю випадково
            return random.choice(available_posts)
        
        elif mode == "randomsmart":
            # Випадково, але виключаючи останні N
            smart_n = int(await db.get_setting("smart_n", "100"))
            recent_published = await db.get_published_post_ids(limit=smart_n)
            
            # Фільтруємо пости які були опубліковані недавно
            smart_available = [pid for pid in available_posts if pid not in recent_published]
            
            if not smart_available:
                # Якщо всі пости були недавно, беремо з доступних
                smart_available = available_posts
            
            return random.choice(smart_available)
        
        return None
    
    async def copy_post(self, message_id: int) -> bool:
        """Копіювання поста з джерела в ціль"""
        test_mode = await db.get_setting("test_mode", "0") == "1"
        target_chat_id = ADMIN_ID if test_mode else TARGET_CHANNEL_ID
        
        for attempt in range(self.retry_attempts):
            try:
                # Отримуємо повідомлення через Telethon
                message = await telegram_client.get_message_by_id(SOURCE_CHANNEL, message_id)
                
                if not message:
                    logger.warning(f"Пост {message_id} не знайдено")
                    await send_admin_notification(
                        self.bot,
                        f"⚠️ Пропущено пост {message_id}\n\n"
                        f"Причина: пост не знайдено\n"
                        f"Бот продовжує роботу."
                    )
                    return False
                
                # Перевіряємо чи є медіа
                if not message.media:
                    await send_admin_notification(
                        self.bot,
                        f"⚠️ Пропущено пост {message_id}\n\n"
                        f"Причина: текстовий пост без медіа\n"
                        f"Бот продовжує роботу."
                    )
                    return False
                
                # Визначаємо тип медіа
                from telethon.tl.types import (
                    MessageMediaPhoto, MessageMediaDocument,
                    MessageMediaWebPage, DocumentAttributeVideo,
                    DocumentAttributeAnimated, DocumentAttributeSticker
                )
                
                # Перевіряємо чи це альбом (MediaGroup)
                if message.grouped_id:
                    return await self._process_media_group(message, target_chat_id)
                
                # Одиночне медіа
                original_caption = message.message or ""
                has_spoiler = has_blur_marker(original_caption)
                
                # Завантажуємо медіа
                media_bytes = await telegram_client.download_media(message)
                if not media_bytes:
                    logger.error(f"Не вдалося завантажити медіа для поста {message_id}")
                    return False
                
                # Формуємо фінальний caption
                final_caption = await self._get_final_caption(original_caption)
                
                # Отримуємо кнопки
                reply_markup = await self._get_reply_markup()
                
                # Визначаємо тип і відправляємо
                if isinstance(message.media, MessageMediaPhoto):
                    # Фото
                    photo_file = BufferedInputFile(media_bytes, filename="photo.jpg")
                    result = await self.bot.send_photo(
                        chat_id=target_chat_id,
                        photo=photo_file,
                        caption=final_caption,
                        reply_markup=reply_markup,
                        has_spoiler=has_spoiler
                    )
                
                elif isinstance(message.media, MessageMediaDocument):
                    # Документ (відео, гіфка, файл)
                    doc = message.media.document
                    
                    # Перевіряємо атрибути
                    is_video = False
                    is_animation = False
                    
                    for attr in doc.attributes:
                        if isinstance(attr, DocumentAttributeVideo):
                            is_video = True
                        elif isinstance(attr, DocumentAttributeAnimated):
                            is_animation = True
                    
                    if is_animation:
                        # Гіфка
                        animation_file = BufferedInputFile(media_bytes, filename="animation.gif")
                        result = await self.bot.send_animation(
                            chat_id=target_chat_id,
                            animation=animation_file,
                            caption=final_caption,
                            reply_markup=reply_markup,
                            has_spoiler=has_spoiler
                        )
                    elif is_video:
                        # Відео
                        video_file = BufferedInputFile(media_bytes, filename="video.mp4")
                        result = await self.bot.send_video(
                            chat_id=target_chat_id,
                            video=video_file,
                            caption=final_caption,
                            reply_markup=reply_markup,
                            has_spoiler=has_spoiler
                        )
                    else:
                        # Інший документ
                        document_file = BufferedInputFile(media_bytes, filename="document")
                        result = await self.bot.send_document(
                            chat_id=target_chat_id,
                            document=document_file,
                            caption=final_caption,
                            reply_markup=reply_markup
                        )
                else:
                    logger.warning(f"Невідомий тип медіа для поста {message_id}")
                    return False
                
                # Зберігаємо в базу
                await db.add_published_post(message_id, result.message_id)
                
                logger.info(f"Успішно опубліковано пост {message_id}")
                return True
                
            except TelegramRetryAfter as e:
                logger.warning(f"Rate limit, чекаємо {e.retry_after} секунд")
                await asyncio.sleep(e.retry_after)
                continue
            
            except TelegramBadRequest as e:
                logger.error(f"Telegram API помилка при копіюванні поста {message_id}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delays[attempt])
                    continue
                else:
                    await send_admin_notification(
                        self.bot,
                        f"❌ Помилка публікації поста {message_id}\n\n"
                        f"Причина: {e}\n"
                        f"Бот продовжує роботу."
                    )
                    return False
            
            except Exception as e:
                logger.error(f"Невідома помилка при копіюванні поста {message_id}: {e}")
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delays[attempt])
                    continue
                else:
                    await send_admin_notification(
                        self.bot,
                        f"❌ Критична помилка публікації поста {message_id}\n\n"
                        f"Причина: {e}\n"
                        f"Бот продовжує роботу."
                    )
                    return False
        
        return False
    
    async def _process_media_group(self, message, target_chat_id: int) -> bool:
        """Обробка альбому (MediaGroup)"""
        try:
            # Отримуємо всі повідомлення з тим же grouped_id
            entity = await telegram_client.client.get_entity(SOURCE_CHANNEL)
            
            # Шукаємо всі повідомлення з цим grouped_id
            media_messages = []
            async for msg in telegram_client.client.iter_messages(
                entity, 
                limit=10,
                offset_id=message.id + 5  # Починаємо трохи вище
            ):
                if msg.grouped_id == message.grouped_id and msg.media:
                    media_messages.append(msg)
            
            if not media_messages:
                logger.warning(f"Не вдалося знайти медіа для альбому {message.id}")
                return False
            
            # Сортуємо по ID
            media_messages.sort(key=lambda m: m.id)
            
            # Формуємо медіа групу
            media = []
            original_caption = media_messages[0].message or ""
            has_spoiler = has_blur_marker(original_caption)
            final_caption = await self._get_final_caption(original_caption)
            
            from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument, DocumentAttributeVideo, DocumentAttributeAnimated
            
            for i, msg in enumerate(media_messages):
                media_bytes = await telegram_client.download_media(msg)
                if not media_bytes:
                    continue
                
                # Caption тільки для першого
                caption = final_caption if i == 0 else None
                
                if isinstance(msg.media, MessageMediaPhoto):
                    media.append(InputMediaPhoto(
                        media=BufferedInputFile(media_bytes, filename=f"photo_{i}.jpg"),
                        caption=caption,
                        has_spoiler=has_spoiler
                    ))
                elif isinstance(msg.media, MessageMediaDocument):
                    # Перевіряємо чи це відео
                    is_video = False
                    for attr in msg.media.document.attributes:
                        if isinstance(attr, DocumentAttributeVideo):
                            is_video = True
                            break
                    
                    if is_video:
                        media.append(InputMediaVideo(
                            media=BufferedInputFile(media_bytes, filename=f"video_{i}.mp4"),
                            caption=caption,
                            has_spoiler=has_spoiler
                        ))
                    else:
                        # Інший документ - додаємо як фото (fallback)
                        media.append(InputMediaPhoto(
                            media=BufferedInputFile(media_bytes, filename=f"doc_{i}"),
                            caption=caption,
                            has_spoiler=has_spoiler
                        ))
            
            if not media:
                logger.warning(f"Не вдалося сформувати медіа групу для альбому {message.id}")
                return False
            
            # Відправляємо альбом
            result = await self.bot.send_media_group(
                chat_id=target_chat_id,
                media=media
            )
            
            # Додаємо кнопки до першого повідомлення
            reply_markup = await self._get_reply_markup()
            if reply_markup and result:
                await self.bot.edit_message_reply_markup(
                    chat_id=target_chat_id,
                    message_id=result[0].message_id,
                    reply_markup=reply_markup
                )
            
            # Зберігаємо всі ID альбому
            for msg in result:
                await db.add_published_post(message.id, msg.message_id)
            
            logger.info(f"Успішно опубліковано альбом {message.id} ({len(media)} медіа)")
            return True
            
        except Exception as e:
            logger.error(f"Помилка обробки альбому {message.id}: {e}")
            return False
    
    async def _get_final_caption(self, original_caption: str) -> str:
        """Формування фінального caption"""
        # Отримуємо мульти-підписи
        multi_captions = await db.get_all_captions()
        
        if multi_captions:
            # Випадковий вибір
            bot_caption = random.choice(multi_captions)
        else:
            # Основний підпис
            bot_caption = await db.get_setting("caption", "")
        
        # Формуємо фінальний текст
        if original_caption and bot_caption:
            return f"{original_caption}\n\n{bot_caption}"
        elif bot_caption:
            return bot_caption
        else:
            return original_caption
    
    async def _get_reply_markup(self) -> Optional[InlineKeyboardMarkup]:
        """Отримання кнопок під постом"""
        buttons = await db.get_all_buttons()
        
        if not buttons:
            return None
        
        keyboard = []
        for text, url in buttons:
            keyboard.append([InlineKeyboardButton(text=text, url=url)])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

poster = None