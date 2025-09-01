import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import telebot
import threading
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import start, categories, orders, menu
from panel.app import app as flask_app

def run_flask(bot_instance):
    flask_app.bot = bot_instance
    flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)

if __name__ == "__main__":
    bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

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
