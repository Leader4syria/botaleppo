from bot.utils.api import APIClient

def register_handlers(bot):
    api_client = APIClient()

    @bot.callback_query_handler(func=lambda call: call.data.startswith('service:'))
    def handle_service_selection(call):
        service_id = int(call.data.split(':')[1])
        user_id = call.from_user.id

        order_data = {'service_id': service_id, 'user_id': user_id}

        response = api_client.new_order(order_data)

        if response:
            order_id = response.get('order_id', 'N/A')
            bot.answer_callback_query(call.id)
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=f"تم إنشاء طلبك بنجاح! رقم الطلب: {order_id}"
            )
        else:
            bot.answer_callback_query(call.id, "حدث خطأ أثناء إنشاء الطلب.")
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="عذراً، لم نتمكن من معالجة طلبك."
            )

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
