from bot.keyboards.inline import main_menu_keyboard
from bot.utils.decorators import check_subscription
from bot.handlers.categories import show_all_services_formatted, show_main_categories
from bot.utils.api import APIClient

from bot.utils import db

def show_my_orders(bot, message):
    user_id = message.chat.id
    orders = db.get_orders_for_user(user_id)

    reply_text = "📦 **طلباتي**\n\n"
    if orders:
        for order in orders:
            service_name = order.get('services', {}).get('name', 'N/A')
            order_status = order.get('status', 'pending')
            order_date = order.get('created_at').split('T')[0]
            reply_text += f"- {service_name} ({order_status}) - {order_date}\n"
    else:
        reply_text += "لا يوجد لديك طلبات حالية."

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ العودة إلى القائمة الرئيسية", callback_data="menu:back_to_main"))
    bot.edit_message_text(reply_text, chat_id=message.chat.id, message_id=message.message_id, parse_mode='Markdown', reply_markup=keyboard)


def register_handlers(bot):

    @bot.callback_query_handler(func=lambda call: call.data.startswith('menu:'))
    @check_subscription(bot)
    def handle_menu_callbacks(call):
        action = call.data.split(':')[1]

        if action == 'services':
            # This should show the interactive category menu
            show_main_categories(bot, call.message)

        elif action == 'show_all':
            # This shows the static, formatted list of all services
            show_all_services_formatted(bot, call.message)

        elif action == 'my_info':
            user = call.from_user
            info_text = (
                f"ℹ️ **معلومات حسابك**\n\n"
                f"**الاسم:** {user.first_name}\n"
                f"**المعرف:** @{user.username if user.username else 'غير متوفر'}\n"
                f"**ID:** `{user.id}`"
            )
            # We edit the message to show the info, but keep the main menu keyboard
            bot.edit_message_text(info_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode='Markdown', reply_markup=main_menu_keyboard())

        elif action == 'my_orders':
            bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
            show_my_orders(bot, call.message)

        elif action == 'contact_us':
            contact_text = "للتواصل مع الدعم، يرجى مراسلة المسؤول."
            bot.answer_callback_query(call.id, text=contact_text, show_alert=True)

        elif action == 'back_to_main':
            welcome_text = "أهلاً بك في البوت! اختر أحد الخيارات من القائمة."
            bot.edit_message_text(welcome_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=main_menu_keyboard())
