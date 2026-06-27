from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu(is_running: bool, test_mode: bool) -> InlineKeyboardMarkup:
    """Головне меню"""
    status_emoji = "▶️" if is_running else "⏸"
    test_emoji = "🧪 " if test_mode else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Режим", callback_data="menu_mode"),
            InlineKeyboardButton(text="⏱ Інтервал", callback_data="menu_interval")
        ],
        [
            InlineKeyboardButton(text="✍️ Підпис", callback_data="menu_caption"),
            InlineKeyboardButton(text="🎭 Мульти-підписи", callback_data="menu_captions")
        ],
        [
            InlineKeyboardButton(text="🔘 Кнопки", callback_data="menu_buttons"),
            InlineKeyboardButton(text="📅 Розклад", callback_data="menu_schedule")
        ],
        [
            InlineKeyboardButton(text="📊 Детальніше", callback_data="menu_stats"),
            InlineKeyboardButton(text=f"{test_emoji}🚀 Опублікувати зараз", callback_data="action_publish_now")
        ],
        [
            InlineKeyboardButton(
                text=f"{'⏸ Пауза' if is_running else '▶️ Старт'}", 
                callback_data="action_toggle"
            ),
            InlineKeyboardButton(text="🛠 Сервіс", callback_data="menu_service")
        ],
        [
            InlineKeyboardButton(text="🏓 Ping", callback_data="action_ping")
        ]
    ])
    return keyboard

def get_mode_menu(current_mode: str) -> InlineKeyboardMarkup:
    """Меню вибору режиму"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔢 Послідовно {'✓' if current_mode == 'sequential' else ''}", 
            callback_data="mode_set:sequential"
        )],
        [InlineKeyboardButton(
            text=f"🎲 Випадково {'✓' if current_mode == 'random' else ''}", 
            callback_data="mode_set:random"
        )],
        [InlineKeyboardButton(
            text=f"🧠 RandomSmart {'✓' if current_mode == 'randomsmart' else ''} →", 
            callback_data="mode_smart_settings"
        )],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
    ])
    return keyboard

def get_smart_n_menu(current_n: int) -> InlineKeyboardMarkup:
    """Меню налаштування N для RandomSmart"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="50", callback_data="smart_n:50"),
            InlineKeyboardButton(text="70", callback_data="smart_n:70"),
            InlineKeyboardButton(text="100", callback_data="smart_n:100")
        ],
        [
            InlineKeyboardButton(text="150", callback_data="smart_n:150"),
            InlineKeyboardButton(text="200", callback_data="smart_n:200"),
            InlineKeyboardButton(text="Ввести своє", callback_data="smart_n_custom")
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_mode")]
    ])
    return keyboard

def get_interval_menu(current_interval: int) -> InlineKeyboardMarkup:
    """Меню вибору інтервалу"""
    intervals = [
        (15, "15 хв"),
        (30, "30 хв"),
        (60, "1 год"),
        (120, "2 год"),
        (240, "4 год")
    ]
    
    buttons = []
    row = []
    for minutes, label in intervals:
        suffix = " ✓" if minutes == current_interval else ""
        row.append(InlineKeyboardButton(
            text=f"{label}{suffix}", 
            callback_data=f"interval_set:{minutes}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    
    buttons.append([InlineKeyboardButton(text="Ввести свій (в хвилинах)", callback_data="interval_custom")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_caption_menu(has_caption: bool, has_multi: bool) -> InlineKeyboardMarkup:
    """Меню налаштування підпису"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Змінити основний підпис", callback_data="caption_edit")],
        [InlineKeyboardButton(
            text="🗑 Прибрати підпис" if has_caption else "➕ Додати підпис", 
            callback_data="caption_remove" if has_caption else "caption_edit"
        )],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
    ])
    return keyboard

def get_service_menu(test_mode: bool) -> InlineKeyboardMarkup:
    """Меню сервісу"""
    test_status = "✅ Увімкнено" if test_mode else "❌ Вимкнено"
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🧪 Тестовий режим: {test_status}", 
            callback_data="service_toggle_test"
        )],
        [InlineKeyboardButton(text="📤 Експорт бази", callback_data="service_export")],
        [InlineKeyboardButton(text="📥 Імпорт бази", callback_data="service_import")],
        [InlineKeyboardButton(text="🗑 Очистити історію", callback_data="service_clear")],
        [InlineKeyboardButton(text="📋 Надіслати логи", callback_data="service_logs")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu_main")]
    ])
    return keyboard

def get_confirm_keyboard(action: str) -> InlineKeyboardMarkup:
    """Клавіатура підтвердження"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Так", callback_data=f"confirm_yes:{action}"),
            InlineKeyboardButton(text="❌ Ні", callback_data=f"confirm_no:{action}")
        ]
    ])
    return keyboard

def get_back_button(callback_data: str = "menu_main") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=callback_data)]
    ])
    return keyboard