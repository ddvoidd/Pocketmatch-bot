import json
from datetime import datetime
from telegram.ext import MessageHandler, filters
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from keyboards import get_profile_keyboard, get_edit_profile_keyboard, get_back_to_profile_keyboard, get_gender_keyboard, get_target_gender_keyboard, get_main_menu_keyboard

async def show_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает профиль пользователя"""
    db = context.bot_data['db']
    user_id = update.effective_user.id

    profile = db.get_profile(user_id)
    if not profile:
        await update.message.reply_text(
            "У тебя еще нет профиля. Напиши /start чтобы создать его!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    gender_display = {
        'male': '👨 Мужской',
        'female': '👩 Женский',
        'other': '🔮 Другой'
    }.get(profile['gender'], '🔮 Другой')

    target_display = {
        'male': '👨 Парня',
        'female': '👩 Девушку',
        'all': '👥 Всех'
    }.get(profile['target_gender'], '👥 Всех')

    profile_text = (
        f"👤 <b>Твой профиль</b>\n\n"
        f"📝 <b>Имя:</b> {profile['name']}\n"
        f"🎂 <b>Возраст:</b> {profile['age']}\n"
        f"⚧ <b>Пол:</b> {gender_display}\n"
        f"🎯 <b>Ищу:</b> {target_display}\n"
        f"🏙 <b>Город:</b> {profile['city']}\n"
        f"📖 <b>О себе:</b> {profile['bio'] or 'Не указано'}\n"
        f"📸 <b>Фото:</b> {'✅ Есть' if profile['photos'] else '❌ Нет'}\n"
        f"👁 <b>Статус:</b> {'✅ Активна' if profile['is_active'] else '❌ Неактивна'}"
    )

    if profile['photos']:
        await update.message.reply_photo(
            photo=profile['photos'][0],
            caption=profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode='HTML'
        )
    else:
        await update.message.reply_text(
            profile_text,
            reply_markup=get_profile_keyboard(),
            parse_mode='HTML'
        )

async def handle_profile_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действия в профиле"""
    text = update.message.text
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if not db.profile_exists(user_id):
        await update.message.reply_text(
            "У тебя еще нет профиля. Напиши /start чтобы создать его!",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if text == '✏️ Редактировать профиль':
        await show_edit_menu(update, context)

    elif text == '◀️ Назад к профилю':
        context.user_data.pop('adding_photo', None)
        context.user_data.pop('managing_photos', None)
        context.user_data.pop('editing_field', None)
        await show_profile(update, context)

    elif text == '◀️ Назад в меню':
        context.user_data.pop('adding_photo', None)
        context.user_data.pop('managing_photos', None)
        context.user_data.pop('editing_field', None)
        await update.message.reply_text(
            "Возвращаемся в главное меню:",
            reply_markup=get_main_menu_keyboard()
        )

    else:
        await show_profile(update, context)

async def handle_photo_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает добавление фото через управление профилем"""
    if (context.user_data.get('adding_photo') or context.user_data.get('managing_photos')) and update.message.photo:
        photo = update.message.photo[-1]
        photo_file_id = photo.file_id

        db = context.bot_data['db']
        user_id = update.effective_user.id

        print(f"🔍 DEBUG: Добавление фото в профиль, user_id={user_id}")

        with db.get_connection() as conn:
            conn.execute(
                'UPDATE profiles SET photos = ?, updated_at = ? WHERE user_id = ?',
                (json.dumps([photo_file_id]), datetime.now().isoformat(), user_id)
            )

        print(f"🔍 DEBUG: Фото обновлено в базе данных")

        profile = db.get_profile(user_id)
        print(f"🔍 DEBUG: Фото в профиле после обновления: {len(profile['photos'])}")

        await update.message.reply_text(
            "✅ Фото успешно обновлено!",
            reply_markup=get_profile_keyboard()
        )

        context.user_data.pop('adding_photo', None)
        context.user_data.pop('managing_photos', None)

        await show_profile(update, context)
        return

    print(f"🔍 DEBUG: Фото не обработано в profile.py, состояния: adding_photo={context.user_data.get('adding_photo')}, managing_photos={context.user_data.get('managing_photos')}")

async def show_edit_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает меню редактирования"""
    await update.message.reply_text(
        "✏️ <b>Редактирование профиля</b>\n\n"
        "Что ты хочешь изменить?",
        reply_markup=get_edit_profile_keyboard(),
        parse_mode='HTML'
    )

async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор поля для редактирования"""
    text = update.message.text
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if text == '📷 Управление фото':
        profile = db.get_profile(user_id)
        photo_count = len(profile['photos'])

        if photo_count >= 1:
            keyboard = [
                [KeyboardButton("🗑 Удалить текущее фото")],
                [KeyboardButton("◀️ Назад к профилю")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

            await update.message.reply_text(
                f"📸 У тебя уже есть фото в анкете.\n"
                "Хочешь удалить текущее фото и заменить на новое?",
                reply_markup=reply_markup
            )
            context.user_data['managing_photos'] = True
        else:
            await update.message.reply_text(
                "📸 В твоей анкете еще нет фото.\n"
                "Отправь мне фото чтобы добавить его в анкету:",
                reply_markup=get_back_to_profile_keyboard()
            )
            context.user_data['adding_photo'] = True

    elif text == '🗑 Удалить текущее фото':
        db = context.bot_data['db']
        user_id = update.effective_user.id

        with db.get_connection() as conn:
            conn.execute(
                'UPDATE profiles SET photos = ?, updated_at = ? WHERE user_id = ?',
                (json.dumps([]), datetime.now().isoformat(), user_id)
            )

        await update.message.reply_text(
            "✅ Текущее фото удалено! Теперь отправь новое фото:",
            reply_markup=get_back_to_profile_keyboard()
        )
        context.user_data['adding_photo'] = True
        context.user_data.pop('managing_photos', None)

    elif text in ['✏️ Имя', '🎂 Возраст', '⚧ Пол', '🎯 Кого ищу', '🏙 Город', '📖 О себе']:
        field_map = {
            '✏️ Имя': 'name',
            '🎂 Возраст': 'age',
            '⚧ Пол': 'gender',
            '🎯 Кого ищу': 'target_gender',
            '🏙 Город': 'city',
            '📖 О себе': 'bio'
        }

        field = field_map.get(text)
        if field:
            context.user_data['editing_field'] = field

            if field == 'gender':
                await update.message.reply_text(
                    "Выбери новый пол:",
                    reply_markup=get_gender_keyboard()
                )
            elif field == 'target_gender':
                await update.message.reply_text(
                    "Выбери, кого ты ищешь:",
                    reply_markup=get_target_gender_keyboard()
                )
            else:
                prompt = {
                    'name': "Введи новое имя:",
                    'age': "Введи новый возраст:",
                    'city': "Введи новый город:",
                    'bio': "Введи новое описание:"
                }.get(field, "Введи новое значение:")

                await update.message.reply_text(
                    prompt,
                    reply_markup=get_back_to_profile_keyboard()
                )

    elif text == '◀️ Назад к профилю':
        context.user_data.pop('managing_photos', None)
        context.user_data.pop('adding_photo', None)
        await show_profile(update, context)

async def handle_edit_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод новых данных"""
    field = context.user_data.get('editing_field')
    text = update.message.text
    db = context.bot_data['db']
    user_id = update.effective_user.id

    if not field:
        await show_profile(update, context)
        return

    if field == 'name' and len(text) < 2:
        await update.message.reply_text("Имя должно быть не короче 2 символов. Попробуй еще раз:")
        return

    elif field == 'age':
        try:
            age = int(text)
            if age < 16 or age > 100:
                await update.message.reply_text("Возраст должен быть от 16 до 100 лет. Попробуй еще раз:")
                return
            text = str(age)
        except ValueError:
            await update.message.reply_text("Пожалуйста, введи число. Попробуй еще раз:")
            return

    elif field == 'gender':
        gender_map = {
            '👨 Мужской': 'male',
            '👩 Женский': 'female',
            '🔮 Другой': 'other'
        }
        text = gender_map.get(text, 'other')

    elif field == 'target_gender':
        target_map = {
            '👨 Парня': 'male',
            '👩 Девушку': 'female',
            '👥 Всех': 'all'
        }
        text = target_map.get(text, 'all')

    elif field == 'city' and len(text) < 2:
        await update.message.reply_text("Название города должно быть не короче 2 символов. Попробуй еще раз:")
        return

    if db.update_profile_field(user_id, field, text):
        await update.message.reply_text(
            "✅ Изменения сохранены!",
            reply_markup=get_profile_keyboard()
        )

        await show_profile(update, context)
    else:
        await update.message.reply_text(
            "❌ Не удалось сохранить изменения. Попробуй еще раз.",
            reply_markup=get_profile_keyboard()
        )

    context.user_data.pop('editing_field', None)

profile_handler = MessageHandler(filters.Regex('^(👤 Мой профиль)$'), show_profile)
profile_actions_handler = MessageHandler(
    filters.Regex('^(✏️ Редактировать профиль|◀️ Назад к профилю|◀️ Назад в меню)$'),
    handle_profile_actions
)
edit_choice_handler = MessageHandler(
    filters.Regex('^(✏️ Имя|🎂 Возраст|⚧ Пол|🎯 Кого ищу|🏙 Город|📖 О себе|📷 Управление фото|🗑 Удалить текущее фото)$'),
    handle_edit_choice
)