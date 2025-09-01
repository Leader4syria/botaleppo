from bot.utils import db
from bot.config import ADMIN_ID
from bot.utils.decorators import check_subscription
from bot.keyboards.inline import main_menu_keyboard

def register_handlers(bot):
    @bot.message_handler(commands=['start'])
    @check_subscription(bot)
    def send_welcome(message):
        user = message.from_user

        # Check if user is new and notify admin
        existing_user = db.get_user(user.id)
        if not existing_user:
            db.add_user(user.id, user.first_name, user.username)
            if ADMIN_ID:
                admin_message = (
                    f"👤 مستخدم جديد بدأ استخدام البوت!\n\n"
                    f"الاسم: {user.first_name}\n"
                    f"المعرف: @{user.username or 'N/A'}\n"
                    f"ID: `{user.id}`"
                )
                bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')

        # Send the main menu
        balance = existing_user.get('balance', 0.0) if existing_user else 0.0
        welcome_text = (
            f"أهلاً بك يا {user.first_name}!\n\n"
            f"👤 معرفك: `{user.id}`\n"
            f"💰 رصيدك الحالي: `{balance:.2f}`\n\n"
            "اختر أحد الخيارات من القائمة:"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu_keyboard(), parse_mode='Markdown')
