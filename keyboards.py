from telegram import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    keyboard = [
        [KeyboardButton("👀 Искать пару")],
        [KeyboardButton("👤 Мой профиль"), KeyboardButton("💌 Мои мэтчи")],
        [KeyboardButton("⚙️ Настройки")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_gender_keyboard():
    keyboard = [
        [KeyboardButton("👨 Мужской"), KeyboardButton("👩 Женский")],
        [KeyboardButton("🔮 Другой")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_target_gender_keyboard():
    keyboard = [
        [KeyboardButton("👨 Парня"), KeyboardButton("👩 Девушку")],
        [KeyboardButton("👥 Всех")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_cancel_keyboard():
    keyboard = [
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_skip_keyboard():
    keyboard = [
        [KeyboardButton("⏭️ Пропустить")],
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_photo_keyboard():
    keyboard = [
        [KeyboardButton("✅ Завершить регистрацию")],
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_photo_only_keyboard():
    """Клавиатура только с кнопкой отмены (до добавления первого фото)"""
    keyboard = [
        [KeyboardButton("❌ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_settings_keyboard(is_active):
    status = "✅ ВКЛЮЧЕНА" if is_active else "❌ ВЫКЛЮЧЕНA"
    action = "❌ Выключить анкету" if is_active else "✅ Включить анкету"

    keyboard = [
        [KeyboardButton(f"👤 Анкета: {status}")],
        [KeyboardButton(action)],
        [KeyboardButton("◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_profile_keyboard():
    keyboard = [
        [KeyboardButton("✏️ Редактировать профиль")],
        [KeyboardButton("◀️ Назад в меню")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_edit_profile_keyboard():
    keyboard = [
        [KeyboardButton("✏️ Имя"), KeyboardButton("🎂 Возраст")],
        [KeyboardButton("⚧ Пол"), KeyboardButton("🎯 Кого ищу")],
        [KeyboardButton("🏙 Город"), KeyboardButton("📖 О себе")],
        [KeyboardButton("📷 Управление фото")],
        [KeyboardButton("◀️ Назад к профилю")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_back_to_profile_keyboard():
    keyboard = [
        [KeyboardButton("◀️ Назад к профилю")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)