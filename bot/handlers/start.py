from bot.handlers.categories import show_main_categories

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        show_main_categories(bot, message.chat.id)
