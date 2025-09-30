from telegram.ext import MessageHandler, CallbackQueryHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from keyboards import get_main_menu_keyboard

async def send_message_safe(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, reply_markup=None):
    """Безопасная отправка сообщения для любого типа update"""
    if hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.message.reply_text(text, reply_markup=reply_markup)
        except:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=text,
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

async def show_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает лайки пользователя"""
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if not db.profile_exists(user_id):
        await send_message_safe(
            update,
            context,
            "Сначала создай профиль командой /start",
            reply_markup=get_main_menu_keyboard()
        )
        return

    likes = db.get_user_likes(user_id)

    if not likes:
        await send_message_safe(
            update,
            context,
            "💔 У тебя пока нет лайков. Продолжай искать - обязательно найдутся взаимные симпатии!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await show_like(update, context, likes, 0)

async def show_like(update: Update, context: ContextTypes.DEFAULT_TYPE, likes, index):
    """Показывает конкретный лайк"""
    if index >= len(likes):
        message_text = "📋 Это все твои лайки! Возвращаемся в главное меню:"

        if hasattr(update, 'callback_query') and update.callback_query:
            try:
                await update.callback_query.message.reply_text(
                    message_text,
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=message_text,
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await update.message.reply_text(
                message_text,
                reply_markup=get_main_menu_keyboard()
            )
        return

    like = likes[index]
    db = context.bot_data['db']

    is_match = db.get_match(update.effective_user.id, like['to_user_id'])

    profile_text = (
        f"💝 Лайк от {like['to_user_name']}, {like['to_user_age']}\n"
        f"💬 {'✅ Взаимная симпатия!' if is_match else '❌ Ждем ответа...'}"
    )

    keyboard = []
    if is_match:
        if like.get('to_username'):
            keyboard.append([InlineKeyboardButton(
                "💌 Написать в Telegram",
                url=f"https://t.me/{like['to_username']}"
            )])
        else:
            keyboard.append([InlineKeyboardButton(
                "💌 Написать сообщение",
                callback_data=f"no_username_{like['to_user_id']}"
            )])

    if index > 0:
        if keyboard and len(keyboard[-1]) < 2:
            keyboard[-1].append(InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_like_{index-1}"))
        else:
            keyboard.append([InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_like_{index-1}")])

    if index < len(likes) - 1:
        if keyboard and keyboard[-1] and len(keyboard[-1]) < 2:
            keyboard[-1].append(InlineKeyboardButton("Дальше ➡️", callback_data=f"next_like_{index+1}"))
        else:
            keyboard.append([InlineKeyboardButton("Дальше ➡️", callback_data=f"next_like_{index+1}")])

    keyboard.append([InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.message.delete()
        except:
            pass

        if like['photos']:
            try:
                await context.bot.send_photo(
                    chat_id=update.effective_user.id,
                    photo=like['photos'][0],
                    caption=profile_text,
                    reply_markup=reply_markup
                )
            except:
                await context.bot.send_message(
                    chat_id=update.effective_user.id,
                    text=profile_text,
                    reply_markup=reply_markup
                )
        else:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text=profile_text,
                reply_markup=reply_markup
            )
    else:
        if like['photos']:
            try:
                await update.message.reply_photo(
                    photo=like['photos'][0],
                    caption=profile_text,
                    reply_markup=reply_markup
                )
            except:
                await update.message.reply_text(
                    profile_text,
                    reply_markup=reply_markup
                )
        else:
            await update.message.reply_text(
                profile_text,
                reply_markup=reply_markup
            )

async def handle_no_username(update: Update, context: ContextTypes.DEFAULT_TYPE, target_user_id: int):
    """Обрабатывает случай когда у мэтча нет username"""
    db = context.bot_data['db']

    target_profile = db.get_profile(target_user_id)

    try:
        await update.callback_query.message.delete()
    except:
        pass

    await context.bot.send_message(
        chat_id=update.effective_user.id,
        text=(
            f"💌 Нельзя написать {target_profile['name']} напрямую\n\n"
            f"❌ У пользователя не установлен Telegram username\n\n"
            f"Попроси {target_profile['name']} установить username в настройках Telegram:\n"
            f"1. Открой Telegram → Настройки\n"
            f"2. Выбери 'Имя пользователя'\n"
            f"3. Установи уникальный username\n\n"
            f"После этого можно будет написать напрямую!"
        ),
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад к лайкам", callback_data="back_to_likes")]])
    )

async def handle_matches_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действия в разделе лайков"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    db = context.bot_data['db']

    if data == 'back_to_menu':
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text="Возвращаемся в меню:",
            reply_markup=get_main_menu_keyboard()
        )

    elif data == 'back_to_likes':
        likes = db.get_user_likes(user_id)
        try:
            await query.message.delete()
        except:
            pass
        await show_like(update, context, likes, 0)

    elif data.startswith(('next_like_', 'prev_like_')):
        index = int(data.split('_')[-1])
        likes = db.get_user_likes(user_id)
        try:
            await query.message.delete()
        except:
            pass
        await show_like(update, context, likes, index)

    elif data.startswith('no_username_'):
        target_user_id = int(data.split('_')[2])
        await handle_no_username(update, context, target_user_id)

matches_handler = MessageHandler(filters.Regex('^(💌 Мои мэтчи)$'), show_matches)
matches_actions_handler = CallbackQueryHandler(handle_matches_actions, pattern="^(next_like_|prev_like_|back_to_menu|no_username_|back_to_likes)")