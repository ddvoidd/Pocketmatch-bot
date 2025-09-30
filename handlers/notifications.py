from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler
from keyboards import get_main_menu_keyboard

async def send_like_notification(context: ContextTypes.DEFAULT_TYPE, to_user_id: int, from_user_id: int):
    """Отправляет уведомление о новом лайке"""
    db = context.bot_data['db']

    from_profile = db.get_profile(from_user_id)
    if not from_profile:
        return

    gender_text = {
        'male': 'парню',
        'female': 'девушке',
        'other': 'пользователю'
    }.get(from_profile['gender'], 'пользователю')

    notification_text = (
        f"💝 Вы понравились {gender_text}!\n\n"
        f"Хотите посмотреть кто это?"
    )

    keyboard = [
        [InlineKeyboardButton("👀 Посмотреть кто это", callback_data=f"view_liker_{from_user_id}")],
        [InlineKeyboardButton("💌 Мои лайки", callback_data="my_likes")]
    ]

    await context.bot.send_message(
        chat_id=to_user_id,
        text=notification_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def send_match_notification(context: ContextTypes.DEFAULT_TYPE, user1_id: int, user2_id: int):
    """Отправляет уведомление о мэтче обоим пользователям"""
    db = context.bot_data['db']

    user1_profile = db.get_profile(user1_id)
    user2_profile = db.get_profile(user2_id)

    if user1_profile and user2_profile:
        with db.get_connection() as conn:
            result1 = conn.execute('SELECT username FROM users WHERE user_id = ?', (user1_id,))
            user1_data = result1.fetchone()
            user1_username = user1_data['username'] if user1_data else None

            result2 = conn.execute('SELECT username FROM users WHERE user_id = ?', (user2_id,))
            user2_data = result2.fetchone()
            user2_username = user2_data['username'] if user2_data else None

        match_text1 = (
            f"🎉 У вас мэтч с {user2_profile['name']}!\n\n"
            f"👤 {user2_profile['name']}, {user2_profile['age']}\n"
            f"🏙 {user2_profile['city']}\n\n"
            f"💬 Взаимная симпатия!"
        )

        keyboard1 = []
        if user2_username:
            keyboard1.append([InlineKeyboardButton(
                f"💌 Написать {user2_profile['name']}",
                url=f"https://t.me/{user2_username}"
            )])
        else:
            keyboard1.append([InlineKeyboardButton(
                "💌 Написать сообщение",
                callback_data=f"no_username_{user2_id}"
            )])

        match_text2 = (
            f"🎉 У вас мэтч с {user1_profile['name']}!\n\n"
            f"👤 {user1_profile['name']}, {user1_profile['age']}\n"
            f"🏙 {user1_profile['city']}\n\n"
            f"💬 Взаимная симпатия!"
        )

        keyboard2 = []
        if user1_username:
            keyboard2.append([InlineKeyboardButton(
                f"💌 Написать {user1_profile['name']}",
                url=f"https://t.me/{user1_username}"
            )])
        else:
            keyboard2.append([InlineKeyboardButton(
                "💌 Написать сообщение",
                callback_data=f"no_username_{user1_id}"
            )])

        try:
            if user2_profile['photos']:
                await context.bot.send_photo(
                    chat_id=user1_id,
                    photo=user2_profile['photos'][0],
                    caption=match_text1,
                    reply_markup=InlineKeyboardMarkup(keyboard1)
                )
            else:
                await context.bot.send_message(
                    chat_id=user1_id,
                    text=match_text1,
                    reply_markup=InlineKeyboardMarkup(keyboard1)
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user1_id}: {e}")

        try:
            if user1_profile['photos']:
                await context.bot.send_photo(
                    chat_id=user2_id,
                    photo=user1_profile['photos'][0],
                    caption=match_text2,
                    reply_markup=InlineKeyboardMarkup(keyboard2)
                )
            else:
                await context.bot.send_message(
                    chat_id=user2_id,
                    text=match_text2,
                    reply_markup=InlineKeyboardMarkup(keyboard2)
                )
        except Exception as e:
            print(f"Ошибка отправки уведомления пользователю {user2_id}: {e}")

async def handle_notification_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действия в уведомлениях"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id
    db = context.bot_data['db']

    if data.startswith('view_liker_'):
        from_user_id = int(data.split('_')[2])
        from_profile = db.get_profile(from_user_id)

        if from_profile:
            with db.get_connection() as conn:
                result = conn.execute('SELECT username FROM users WHERE user_id = ?', (from_user_id,))
                user_data = result.fetchone()
                from_username = user_data['username'] if user_data else None

            gender_display = {
                'male': '👨 Парень',
                'female': '👩 Девушка',
                'other': '🔮 Другое'
            }.get(from_profile['gender'], '🔮 Другое')

            target_display = {
                'male': '👨 парня',
                'female': '👩 девушку',
                'all': '👥 всех'
            }.get(from_profile['target_gender'], '👥 всех')

            profile_text = (
                f"👤 {from_profile['name']}, {from_profile['age']}\n"
                f"⚧ {gender_display}\n"
                f"🏙 {from_profile['city']}\n"
                f"📖 {from_profile['bio'] or 'Описание не указано'}\n"
                f"💝 Ищет: {target_display}\n\n"
                f"💝 Этот пользователь лайкнул вашу анкету!"
            )

            has_liked = db.has_liked(user_id, from_user_id)

            is_match = db.get_match(user_id, from_user_id)

            print(f"🔍 DEBUG view_liker:")
            print(f"   - user_id: {user_id}")
            print(f"   - from_user_id: {from_user_id}")
            print(f"   - has_liked: {has_liked}")
            print(f"   - is_match: {is_match}")

            keyboard = []

            if not is_match and not has_liked:
                print("🔍 Показываем кнопки Лайкнуть/Отклонить")
                keyboard.append([
                    InlineKeyboardButton("❤️ Лайкнуть взамен", callback_data=f"like_back_{from_user_id}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"reject_{from_user_id}")
                ])
            elif is_match:
                print("🔍 Уже есть мэтч, показываем кнопку Написать")
                profile_text += "\n\n🎉 У вас взаимная симпатия!"
                if from_username:
                    keyboard.append([InlineKeyboardButton(
                        f"💌 Написать {from_profile['name']}",
                        url=f"https://t.me/{from_username}"
                    )])
                else:
                    keyboard.append([InlineKeyboardButton(
                        "💌 Написать сообщение",
                        callback_data=f"no_username_{from_user_id}"
                    )])
            elif has_liked:
                print("🔍 Пользователь уже лайкнул, показываем сообщение")
                profile_text += "\n\n❤️ Вы уже лайкнули этого пользователя. Ждем ответа!"

            keyboard.extend([
                [InlineKeyboardButton("💌 Мои лайки", callback_data="my_likes")],
                [InlineKeyboardButton("◀️ В меню", callback_data="back_to_menu")]
            ])

            try:
                await query.message.delete()
            except:
                pass

            if from_profile['photos']:
                try:
                    await context.bot.send_photo(
                        chat_id=user_id,
                        photo=from_profile['photos'][0],
                        caption=profile_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
                except Exception as e:
                    print(f"Ошибка отправки фото: {e}")
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=profile_text,
                        reply_markup=InlineKeyboardMarkup(keyboard)
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=profile_text,
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
        else:
            await query.answer("❌ Анкета не найдена", show_alert=True)

    elif data.startswith('like_back_'):
        target_user_id = int(data.split('_')[2])

        print(f"🔍 DEBUG like_back:")
        print(f"   - user_id: {user_id}")
        print(f"   - target_user_id: {target_user_id}")

        already_liked = db.has_liked(user_id, target_user_id)

        if already_liked:
            await query.answer("❌ Вы уже лайкали этого пользователя", show_alert=True)
            return

        is_match = db.add_like(user_id, target_user_id)

        print(f"🔍 После добавления лайка - is_match: {is_match}")

        try:
            await query.message.delete()
        except:
            pass

        if is_match:
            await send_match_notification(context, user_id, target_user_id)

            await context.bot.send_message(
                chat_id=user_id,
                text="🎉 Теперь у вас мэтч! Взаимная симпатия!",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💌 Написать", callback_data=f"chat_{target_user_id}")
                ]])
            )
        else:
            await context.bot.send_message(
                chat_id=user_id,
                text="❤️ Вы ответили лайком! Ждем ответа...",
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("💌 Мои лайки", callback_data="my_likes")
                ]])
            )

    elif data.startswith('reject_'):
        target_user_id = int(data.split('_')[1])

        try:
            await query.message.delete()
        except:
            pass

        await context.bot.send_message(
            chat_id=user_id,
            text="❌ Лайк отклонен. Продолжайте поиск!",
            reply_markup=get_main_menu_keyboard()
        )

    elif data == 'my_likes':
        from handlers.matches import show_matches
        try:
            await query.message.delete()
        except:
            pass
        await show_matches(update, context)

    elif data == 'back_to_menu':
        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=user_id,
            text="Возвращаемся в меню:",
            reply_markup=get_main_menu_keyboard()
        )

    elif data.startswith('chat_'):
        target_user_id = int(data.split('_')[1])

        with db.get_connection() as conn:
            result = conn.execute('SELECT username FROM users WHERE user_id = ?', (target_user_id,))
            user_data = result.fetchone()
            target_username = user_data['username'] if user_data else None

        target_profile = db.get_profile(target_user_id)

        if target_profile and target_username:
            try:
                await query.message.delete()
            except:
                pass
            await context.bot.send_message(
                chat_id=user_id,
                text=f"💌 Напиши {target_profile['name']} в Telegram:\n\n"
                     f"👉 @{target_username}",
                reply_markup=get_main_menu_keyboard()
            )
        else:
            await query.answer("❌ У пользователя не установлен username", show_alert=True)

    elif data.startswith('no_username_'):
        target_user_id = int(data.split('_')[2])
        target_profile = db.get_profile(target_user_id)

        try:
            await query.message.delete()
        except:
            pass
        await context.bot.send_message(
            chat_id=user_id,
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

    elif data == 'back_to_likes':
        from handlers.matches import show_matches
        try:
            await query.message.delete()
        except:
            pass
        await show_matches(update, context)

notification_actions_handler = CallbackQueryHandler(
    handle_notification_actions,
    pattern="^(view_liker_|like_back_|reject_|my_likes|back_to_menu|chat_|no_username_|back_to_likes)"
)