from telegram.ext import MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes

from keyboards import get_settings_keyboard, get_main_menu_keyboard

async def show_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает настройки"""
    db = context.bot_data['db']
    user_id = update.effective_user.id

    profile = db.get_profile(user_id)
    if not profile:
        await update.message.reply_text(
            "Сначала создай профиль командой /start",
            reply_markup=get_main_menu_keyboard()
        )
        return

    is_active = profile['is_active']
    status = "включена" if is_active else "выключена"
    visibility = "видят" if is_active else "не видят"

    await update.message.reply_text(
        f"⚙️ <b>Настройки</b>\n\n"
        f"Твоя анкета сейчас <b>{status}</b>.\n"
        f"Другие пользователи <b>{visibility}</b> тебя в поиске.\n\n"
        f"Что хочешь сделать?",
        reply_markup=get_settings_keyboard(is_active),
        parse_mode='HTML'
    )

async def handle_settings_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действия в настройках"""
    text = update.message.text
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if not db.profile_exists(user_id):
        await update.message.reply_text(
            "Сначала создай профиль командой /start",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if text == '◀️ Назад в меню':
        await update.message.reply_text(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )
        return

    elif text in ['✅ Включить анкету', '❌ Выключить анкету']:
        is_active = text == '✅ Включить анкету'
        db.set_profile_active(user_id, is_active)

        status = "включена" if is_active else "выключена"
        visibility = "видят" if is_active else "не видят"

        await update.message.reply_text(
            f"✅ <b>Готово!</b>\n\n"
            f"Твоя анкета теперь <b>{status}</b>.\n"
            f"Другие пользователи <b>{visibility}</b> тебя в поиске.",
            reply_markup=get_settings_keyboard(is_active),
            parse_mode='HTML'
        )

    elif text == '⚙️ Настройки':
        await show_settings(update, context)

    else:
        profile = db.get_profile(user_id)
        if profile:
            await show_settings(update, context)

settings_handler = MessageHandler(filters.Regex('^(⚙️ Настройки)$'), show_settings)
settings_actions_handler = MessageHandler(
    filters.Regex('^(◀️ Назад в меню|✅ Включить анкету|❌ Выключить анкету|👤 Анкета: .*)$'),
    handle_settings_actions
)