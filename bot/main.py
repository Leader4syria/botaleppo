import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import telebot
import threading
import traceback
from bot.config import TELEGRAM_BOT_TOKEN, ADMIN_ID
from bot.handlers import start, categories, orders, menu
from panel.app import app as flask_app

def run_flask(bot_instance):
    flask_app.bot = bot_instance
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        if ADMIN_ID:
            error_message = f"ameybot\n\n{traceback.format_exc()}"
            # Split the message if it's too long for Telegram
            for i in range(0, len(error_message), 4096):
                bot.send_message(ADMIN_ID, error_message[i:i+4096])
        return True

if __name__ == "__main__":
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, exception_handler=ExceptionHandler())

    flask_thread = threading.Thread(target=run_flask, args=(bot,))
    flask_thread.daemon = True
    flask_thread.start()

    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
    start.register_handlers(bot)
    categories.register_handlers(bot)
    orders.register_handlers(bot)
    menu.register_handlers(bot)

    print("Bot and Flask Panel are running.")
    bot.polling()
