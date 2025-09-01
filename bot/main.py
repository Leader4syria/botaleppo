import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import telebot
import threading
import traceback
from bot.config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from bot.handlers import start, categories, orders, menu
from panel.app import app as flask_app

# This global bot instance is needed for the exception handler
bot = None

def run_flask(bot_instance):
    flask_app.bot = bot_instance
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        if ADMIN_ID and bot is not None:
            error_message = f"BOT CRASH REPORT\n\n{traceback.format_exc()}"
            # Split the message if it's too long for Telegram
            for i in range(0, len(error_message), 4096):
                try:
                    bot.send_message(ADMIN_ID, error_message[i:i+4096])
                except Exception as e:
                    print(f"Failed to send exception report to admin: {e}")
        return True # Keep the bot running

if __name__ == "__main__":
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, exception_handler=ExceptionHandler())

    flask_thread = threading.Thread(target=run_flask, args=(bot,))
    flask_thread.daemon = True
    flask_thread.start()

    # Register all handlers
    start.register_handlers(bot)
    categories.register_handlers(bot)
    orders.register_handlers(bot)
    menu.register_handlers(bot)

    # Start the periodic service updater in a background thread
    from bot.updater import run_periodic_sync
    updater_thread = threading.Thread(target=run_periodic_sync)
    updater_thread.daemon = True
    updater_thread.start()

    print("Bot, Flask Panel, and Service Updater are running.")
    bot.polling()
