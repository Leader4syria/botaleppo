from bot.utils.api import APIClient
from bot.utils import db
from bot.config import ADMIN_ID
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

def register_handlers(bot):
    api_client = APIClient()

    # This dictionary will temporarily store user order data during the conversation
    user_order_data = {}

    @bot.callback_query_handler(func=lambda call: call.data.startswith('service:'))
    def handle_service_selection(call):
        service_id = int(call.data.split(':')[1])

        # We need to get service details from our DB, not the API
        # The db.get_services() returns a list, let's find the specific one
        all_services = db.get_all_data().get('services', [])
        service = next((s for s in all_services if s['id'] == service_id), None)

        if not service:
            bot.answer_callback_query(call.id, "Service not found.")
            return

        user_id = call.from_user.id
        user_order_data[user_id] = {'service': service}

        description = service.get('description', 'No description available.')
        text = f"<b>{service['name']}</b>\n\n{description}"

        keyboard = InlineKeyboardMarkup()
        order_button = InlineKeyboardButton("📝 طلب الخدمة", callback_data=f"order_start:{service_id}")
        keyboard.add(order_button)

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode='HTML'
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith('order_start:'))
    def handle_order_start(call):
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, "الرجاء إدخال الكمية المطلوبة:")
        bot.register_next_step_handler(msg, process_quantity_step)

    def process_quantity_step(message):
        try:
            quantity = int(message.text)
            if quantity <= 0:
                msg = bot.reply_to(message, 'الكمية يجب أن تكون رقماً موجباً. الرجاء المحاولة مرة أخرى.')
                bot.register_next_step_handler(msg, process_quantity_step)
                return

            user_id = message.from_user.id
            user_order_data[user_id]['quantity'] = quantity

            msg = bot.reply_to(message, 'الآن، الرجاء إدخال معرف اللاعب (Player ID):')
            bot.register_next_step_handler(msg, process_player_id_step)

        except ValueError:
            msg = bot.reply_to(message, 'الرجاء إدخال رقم صحيح للكمية.')
            bot.register_next_step_handler(msg, process_quantity_step)

    def process_player_id_step(message):
        player_id = message.text
        user_id = message.from_user.id

        order_info = user_order_data.get(user_id)
        if not order_info:
            bot.reply_to(message, "حدث خطأ ما، يرجى المحاولة مرة أخرى من البداية.")
            return

        service = order_info['service']
        quantity = order_info['quantity']

        bot.reply_to(message, f"جاري تقديم طلبك لخدمة '{service['name']}' بالكمية {quantity} ومعرف اللاعب {player_id}...")

        # Call the API to place the order
        response = api_client.new_order(
            service_id=service['api_service_id'],
            qty=quantity,
            player_id=player_id
        )

        if response and response.get('order_id'):
            order_id = response.get('order_id', 'N/A')
            reply_text = f"✅ تم إنشاء طلبك بنجاح!\nرقم الطلب: {order_id}"
            bot.send_message(message.chat.id, reply_text)
        else:
            # Order failed, check for insufficient funds
            error_message = str(response).lower()
            if "insufficient funds" in error_message:
                # Notify admin
                admin_message = (
                    f"⚠️ فشل طلب بسبب عدم كفاية الرصيد ⚠️\n\n"
                    f"الخدمة: {service['name']} (ID: {service['api_service_id']})\n"
                    f"الكمية: {quantity}\n"
                    f"معرف اللاعب: {player_id}\n"
                    f"معرف المستخدم: {user_id}\n\n"
                    f"الرجاء معالجة الطلب يدويًا."
                )
                if ADMIN_ID:
                    bot.send_message(ADMIN_ID, admin_message)

                # Notify user
                user_reply = "⏳ لقد فشل طلبك بسبب مشكلة في الرصيد، ولكن تم إرسال تفاصيل طلبك إلى المسؤول لمعالجته يدويًا. سيتم إعلامك عند اكتماله."
                bot.send_message(message.chat.id, user_reply)
            else:
                # Generic error for other failures
                reply_text = "❌ حدث خطأ أثناء إنشاء الطلب. يرجى المحاولة مرة أخرى لاحقاً."
                bot.send_message(message.chat.id, reply_text)

        # Clean up user data
        if user_id in user_order_data:
            del user_order_data[user_id]

    @bot.message_handler(commands=['myorders'])
    def my_orders_command(message):
        user_id = message.from_user.id
        orders = api_client.check_orders(user_id)

        if orders and isinstance(orders, list):
            if not orders:
                reply_text = "لا يوجد لديك طلبات حالية."
            else:
                reply_text = "قائمة طلباتك:\n"
                for order in orders:
                    order_id = order.get('id', 'N/A')
                    status = order.get('status', 'N/A')
                    reply_text += f"- طلب رقم {order_id}: {status}\n"
        else:
            reply_text = "عذراً، لم نتمكن من جلب قائمة طلباتك."

        bot.reply_to(message, reply_text)
