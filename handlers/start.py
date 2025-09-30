from telegram.ext import CommandHandler, MessageHandler, filters
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from keyboards import get_main_menu_keyboard, get_gender_keyboard, get_target_gender_keyboard, get_cancel_keyboard, get_photo_keyboard, get_skip_keyboard, get_photo_only_keyboard

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db = context.bot_data['db']

    if not db.user_exists(user.id):
        db.add_user(user.id, user.username, user.first_name, user.last_name)

    if db.profile_exists(user.id):
        await update.message.reply_text(
            f"Привет, {user.first_name}! 👋",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await update.message.reply_text(
            "🎉 Давай создадим твой профиль!\nКак тебя зовут?",
            reply_markup=get_cancel_keyboard()
        )
        context.user_data['registration_step'] = 'name'

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('registration_step')

    if context.user_data.get('adding_photo') or context.user_data.get('managing_photos'):
        from handlers.profile import handle_photo_addition
        await handle_photo_addition(update, context)
        return

    if step == 'photo' and update.message.photo:
        photo = update.message.photo[-1]
        photo_file_id = photo.file_id

        db = context.bot_data['db']
        user_id = update.effective_user.id

        success = db.add_photo_to_profile(user_id, photo_file_id)

        if success:
            profile = db.get_profile(user_id)
            photo_count = len(profile['photos'])

            message_text = f"📸 Фото добавлено! У тебя {photo_count}/1 фото"

            message_text += "\n\nНажми '✅ Завершить регистрацию' чтобы закончить!"

            await update.message.reply_text(
                message_text,
                reply_markup=get_photo_keyboard()
            )
            return

        else:
            await update.message.reply_text(
                "❌ Не удалось добавить фото. Попробуй еще раз:",
                reply_markup=get_photo_only_keyboard()
            )
            return

    return

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data.get('registration_step')
    text = update.message.text

    print(f"DEBUG: Step={step}, Text='{text}'")

    if text == '❌ Отмена':
        context.user_data.clear()
        await update.message.reply_text(
            "Регистрация отменена. Напиши /start чтобы начать заново.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    if text == '✅ Завершить регистрацию':
        db = context.bot_data['db']
        user_id = update.effective_user.id

        profile = db.get_profile(user_id)
        photo_count = len(profile['photos'])

        if photo_count == 0:
            await update.message.reply_text(
                "❌ Сначала нужно добавить фото! Отправь фото:",
                reply_markup=get_photo_only_keyboard()
            )
            return

        gender_display = {
            'male': '👨 Мужской',
            'female': '👩 Женский',
            'other': '🔮 Другой'
        }.get(context.user_data['gender'], '🔮 Другой')

        target_display = {
            'male': '👨 Парня',
            'female': '👩 Девушку',
            'all': '👥 Всех'
        }.get(context.user_data['target_gender'], '👥 Всех')

        profile_text = (
            f"🎊 Поздравляю, {context.user_data['name']}! Твой профиль создан!\n\n"
            f"👤 {context.user_data['name']}, {context.user_data['age']}\n"
            f"⚧ {gender_display}\n"
            f"🎯 Ищу: {target_display}\n"
            f"🏙 {context.user_data['city']}\n"
            f"📸 Фото: {photo_count} шт.\n"
            f"📖 {profile['bio'] if profile['bio'] else 'Описание не добавлено'}\n\n"
            "Чтобы начать поиск пары, нажми кнопку **👀 Искать пару**"
        )

        if photo_count > 0:
            await update.message.reply_photo(
                photo=profile['photos'][0],
                caption=profile_text,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await update.message.reply_text(
                profile_text,
                reply_markup=get_main_menu_keyboard()
            )

        context.user_data.clear()
        return

    if step:
        if step == 'name':
            if len(text) < 2:
                await update.message.reply_text("Имя должно быть не короче 2 символов. Попробуй еще раз:")
                return

            context.user_data['name'] = text
            context.user_data['registration_step'] = 'age'
            await update.message.reply_text(
                f"Приятно познакомиться, {text}! 👋\nСколько тебе лет?"
            )
            return

        elif step == 'age':
            try:
                age = int(text)
                if age < 16:
                    await update.message.reply_text("Извини, но у нас только 16+. Сколько тебе лет?")
                    return
                if age > 100:
                    await update.message.reply_text("Серьезно? 😄 Назови реальный возраст:")
                    return
            except ValueError:
                await update.message.reply_text("Пожалуйста, введи число. Сколько тебе лет?")
                return

            context.user_data['age'] = age
            context.user_data['registration_step'] = 'gender'
            await update.message.reply_text(
                "Какой у тебя пол?",
                reply_markup=get_gender_keyboard()
            )
            return

        elif step == 'gender':
            gender_map = {
                '👨 Мужской': 'male',
                '👩 Женский': 'female',
                '🔮 Другой': 'other'
            }
            gender = gender_map.get(text, 'other')
            context.user_data['gender'] = gender
            context.user_data['registration_step'] = 'target_gender'
            await update.message.reply_text(
                "Кого ты ищешь?",
                reply_markup=get_target_gender_keyboard()
            )
            return

        elif step == 'target_gender':
            target_map = {
                '👨 Парня': 'male',
                '👩 Девушку': 'female',
                '👥 Всех': 'all'
            }
            target_gender = target_map.get(text, 'all')
            context.user_data['target_gender'] = target_gender
            context.user_data['registration_step'] = 'city'
            await update.message.reply_text(
                "Из какого ты города?",
                reply_markup=get_cancel_keyboard()
            )
            return

        elif step == 'city':
            if len(text) < 2:
                await update.message.reply_text("Название города должно быть не короче 2 символов. Попробуй еще раз:")
                return

            context.user_data['city'] = text
            context.user_data['registration_step'] = 'bio'
            await update.message.reply_text(
                "Напиши немного о себе (хобби, интересы, что ищешь):",
                reply_markup=get_skip_keyboard()
            )
            return

        elif step == 'bio':
            bio = text
            if text == '⏭️ Пропустить' or text.lower() == 'пропустить':
                bio = ""

            db = context.bot_data['db']
            user_id = update.effective_user.id

            db.create_profile(
                user_id=user_id,
                name=context.user_data['name'],
                age=context.user_data['age'],
                gender=context.user_data['gender'],
                target_gender=context.user_data['target_gender'],
                city=context.user_data['city'],
                bio=bio
            )

            context.user_data['registration_step'] = 'photo'
            await update.message.reply_text(
                "📸 **Теперь добавь фото в анкету!**\n\n"
                "📷 Фото обязательно для регистрации!\n"
                "Просто отправь мне одно фото.\n\n"
                "После добавления фото появится кнопка '✅ Завершить регистрацию'",
                reply_markup=get_photo_only_keyboard()
            )
            return

    else:
        if context.user_data.get('managing_photos'):
            print(f"🔍 DEBUG: Обработка managing_photos, текст: {text}")
            from handlers.profile import handle_edit_choice
            await handle_edit_choice(update, context)
            return

        if context.user_data.get('adding_photo'):
            print(f"🔍 DEBUG: Обработка adding_photo, текст: {text}")
            if text != '◀️ Назад к профилю':
                await update.message.reply_text(
                    "📷 Пожалуйста, отправь фото для анкеты:",
                    reply_markup=get_back_to_profile_keyboard()
                )
                return
            else:
                from handlers.profile import handle_profile_actions
                await handle_profile_actions(update, context)
                return

        if text in ['✏️ Редактировать профиль', '📷 Управление фото', '◀️ Назад к профилю', '🗑 Удалить текущее фото']:
            print(f"🔍 DEBUG: Обработка кнопок профиля, текст: {text}")
            from handlers.profile import handle_profile_actions
            await handle_profile_actions(update, context)
            return

        if text in ['✏️ Имя', '🎂 Возраст', '⚧ Пол', '🎯 Кого ищу', '🏙 Город', '📖 О себе']:
            from handlers.profile import handle_edit_choice
            await handle_edit_choice(update, context)
            return

        if text in ['⚙️ Настройки', '✅ Включить анкету', '❌ Выключить анкету', '◀️ Назад в меню']:
            from handlers.settings import handle_settings_actions
            await handle_settings_actions(update, context)
            return

        if text == '👤 Мой профиль':
            from handlers.profile import show_profile
            await show_profile(update, context)
            return

        if text == '👀 Искать пару':
            from handlers.search import start_search
            await start_search(update, context)
            return

        if text == '💌 Мои мэтчи':
            from handlers.matches import show_matches
            await show_matches(update, context)
            return

        if context.user_data.get('editing_field'):
            from handlers.profile import handle_edit_input
            await handle_edit_input(update, context)
            return

        await update.message.reply_text(
            "Напиши /start чтобы начать!",
            reply_markup=get_main_menu_keyboard()
        )

start_handler = CommandHandler('start', start_command)
text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
photo_handler = MessageHandler(filters.PHOTO, handle_photo)