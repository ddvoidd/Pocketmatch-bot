from telegram.ext import MessageHandler, CallbackQueryHandler, filters
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from keyboards import get_main_menu_keyboard

class SearchManager:
    def __init__(self):
        self.user_searches = {}

    def get_next_profile(self, user_id):
        """Возвращает следующую анкету для показа"""
        if user_id not in self.user_searches:
            return None

        search_data = self.user_searches[user_id]
        if search_data['current_index'] >= len(search_data['profiles']):
            return None

        profile = search_data['profiles'][search_data['current_index']]
        search_data['current_index'] += 1
        return profile

    def start_search(self, user_id, profiles):
        """Начинает новый поиск"""
        self.user_searches[user_id] = {
            'current_index': 0,
            'profiles': profiles
        }

search_manager = SearchManager()

async def start_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает поиск анкет ТОЛЬКО из своего города"""
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if not db.profile_exists(user_id):
        await update.message.reply_text(
            "Сначала создай профиль командой /start",
            reply_markup=get_main_menu_keyboard()
        )
        return

    profile = db.get_profile(user_id)
    if not profile['is_active']:
        await update.message.reply_text(
            "❌ Твоя анкета выключена. Включи ее в настройках чтобы начать поиск.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    profiles = db.find_profiles_for_user(user_id)

    if not profiles:
        await update.message.reply_text(
            f"😔 В твоем городе ({profile['city']}) пока нет подходящих анкет.\n\n"
            "Попробуй:\n"
            "• Проверить позже - новые пользователи появляются каждый день!\n"
            "• Изменить город в настройках профиля\n"
            "• Рассказать друзьям о боте - чем больше пользователей, тем больше шансов найти пару!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    search_manager.start_search(user_id, profiles)

    await show_next_profile(update, context, user_id)

async def show_next_profile(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id=None):
    """Показывает следующую анкету"""
    if user_id is None:
        user_id = update.effective_user.id

    profile = search_manager.get_next_profile(user_id)

    if not profile:
        db = context.bot_data['db']
        current_profile = db.get_profile(user_id)

        if hasattr(update, 'callback_query') and update.callback_query:
            try:
                await update.callback_query.message.reply_text(
                    f"🎉 Ты просмотрел все доступные анкеты в городе {current_profile['city']}! "
                    f"Загляни позже - появятся новые.",
                    reply_markup=get_main_menu_keyboard()
                )
            except:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 Ты просмотрел все доступные анкеты в городе {current_profile['city']}! "
                         f"Загляни позже - появятся новые.",
                    reply_markup=get_main_menu_keyboard()
                )
        else:
            await update.message.reply_text(
                f"🎉 Ты просмотрел все доступные анкеты в городе {current_profile['city']}! "
                f"Загляни позже - появятся новые.",
                reply_markup=get_main_menu_keyboard()
            )
        return

    gender_display = {
        'male': '👨 Парень',
        'female': '👩 Девушка',
        'other': '🔮 Другое'
    }.get(profile['gender'], '🔮 Другое')

    profile_text = (
        f"👤 {profile['name']}, {profile['age']}\n"
        f"⚧ {gender_display}\n"
        f"🏙 {profile['city']}\n"
        f"📖 {profile['bio'] or 'Описание не указано'}\n\n"
        f"💝 Ищет: {get_target_display(profile['target_gender'])}"
    )

    keyboard = [
        [
            InlineKeyboardButton("❤️ Лайк", callback_data=f"like_{profile['user_id']}"),
            InlineKeyboardButton("➡️ Дальше", callback_data="next")
        ],
        [
            InlineKeyboardButton("⏹️ Стоп", callback_data="stop_search")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if hasattr(update, 'callback_query') and update.callback_query:
        try:
            await update.callback_query.message.delete()
        except:
            pass

        if profile['photos']:
            await context.bot.send_photo(
                chat_id=user_id,
                photo=profile['photos'][0],
                caption=profile_text,
                reply_markup=reply_markup
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text=profile_text,
                reply_markup=reply_markup
            )
    else:
        if profile['photos']:
            await update.message.reply_photo(
                photo=profile['photos'][0],
                caption=profile_text,
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                profile_text,
                reply_markup=reply_markup
            )

async def handle_search_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действия в поиске"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    db = context.bot_data['db']

    if data == 'next':
        await show_next_profile(update, context, user_id)

    elif data == 'stop_search':
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text="⏹️ Поиск остановлен. Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )

    elif data.startswith('like_'):
        target_user_id = int(data.split('_')[1])

        is_match = db.add_like(user_id, target_user_id)

        try:
            await query.message.delete()
        except:
            pass

        if is_match:
            from handlers.notifications import send_match_notification
            await send_match_notification(context, user_id, target_user_id)

            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 У вас мэтч! Взаимная симпатия!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Продолжить поиск", callback_data="next")]])
            )
        else:
            from handlers.notifications import send_like_notification
            await send_like_notification(context, target_user_id, user_id)

            await context.bot.send_message(
                chat_id=user_id,
                text="❤️ Лайк отправлен! Если ответят взаимностью - будет мэтч!",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Смотреть дальше", callback_data="next")]])
            )

def get_target_display(target_gender):
    """Форматирует текст 'кого ищет'"""
    displays = {
        'male': '👨 парня',
        'female': '👩 девушку',
        'all': '👥 всех'
    }
    return displays.get(target_gender, '👥 всех')

search_handler = MessageHandler(filters.Regex('^(👀 Искать пару)$'), start_search)
search_actions_handler = CallbackQueryHandler(handle_search_actions, pattern="^(like_|next|stop_search)")