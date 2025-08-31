import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import telebot
from bot.config import TELEGRAM_BOT_TOKEN
from bot.handlers import start, categories, orders

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

start.register_handlers(bot)
categories.register_handlers(bot)
orders.register_handlers(bot)

if __name__ == "__main__":
    bot.polling()
