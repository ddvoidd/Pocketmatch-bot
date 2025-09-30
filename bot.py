import logging
from telegram.ext import Application
import threading
import time
from datetime import datetime
import pytz

from config import BOT_TOKEN
from database import Database
from handlers import all_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def start_scheduler_thread(db):
    """Запускает планировщик в отдельном потоке"""
    def scheduler_loop():
        logger.info("🕒 Планировщик запущен (проверка каждую минуту)")
        last_reset_day = None

        while True:
            try:
                now = datetime.now(pytz.timezone('Europe/Moscow'))
                current_day = now.date()

                if now.hour == 3 and now.minute == 0:
                    if last_reset_day != current_day:
                        db.clear_likes_history()
                        last_reset_day = current_day
                        logger.info(f"✅ Ежедневный сброс истории выполнен за {current_day}")
                    time.sleep(3660)
                else:
                    time.sleep(60)

            except Exception as e:
                logger.error(f"❌ Ошибка в планировщике: {e}")
                time.sleep(60)

    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    db = Database('dating_bot.db')
    application.bot_data['db'] = db

    for handler in all_handlers:
        application.add_handler(handler)

    start_scheduler_thread(db)

    logger.info("🤖 Бот запущен с ежедневным сбросом истории в 3:00!")
    application.run_polling()

if __name__ == "__main__":
    main()