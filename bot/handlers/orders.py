from bot.utils.api import APIClient
from bot.utils import db
from bot.config import ADMIN_ID
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

def register_handlers(bot):
    user_state = {}

    def ask_next_param(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state or not state.get('params_to_ask'):
            finalize_order(message)
            return

        param_name = state['params_to_ask'][0]
        question = f"الرجاء إدخال '{param_name}':"

        # Check for quantity validation
        # ASSUMPTION: The quantity parameter is named 'qty'
        if param_name.lower() == 'qty':
            qty_rules = state['service'].get('qty_values')
            if qty_rules and isinstance(qty_rules, dict):
                min_qty = qty_rules.get('min')
                max_qty = qty_rules.get('max')
                question += f"\n(الكمية المسموح بها: بين {min_qty} و {max_qty})"

        msg = bot.send_message(user_id, question)
        bot.register_next_step_handler(msg, process_next_param)

    def process_next_param(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state:
            bot.send_message(user_id, "حدث خطأ، يرجى المحاولة من جديد.")
            return

        param_name = state['params_to_ask'][0]

        # Validate quantity if applicable
        if param_name.lower() == 'qty':
            try:
                quantity = int(message.text)
                qty_rules = state['service'].get('qty_values')
                if qty_rules and isinstance(qty_rules, dict):
                    min_qty = int(qty_rules.get('min', 0))
                    max_qty = int(qty_rules.get('max', float('inf')))
                    if not (min_qty <= quantity <= max_qty):
                        bot.reply_to(message, f"الكمية خارج النطاق المسموح به. الرجاء المحاولة مرة أخرى.")
                        ask_next_param(message) # Re-ask the same question
                        return
            except (ValueError, TypeError):
                bot.reply_to(message, "الكمية يجب أن تكون رقماً. الرجاء المحاولة مرة أخرى.")
                ask_next_param(message) # Re-ask
                return

        # Store the valid parameter and remove it from the list to ask
        state['collected_params'][param_name] = message.text
        state['params_to_ask'].pop(0)

        # Ask the next question
        ask_next_param(message)

    def finalize_order(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state or not state.get('service'):
            bot.send_message(user_id, "حدث خطأ أو انتهت مهلة الجلسة. يرجى إعادة بدء الطلب من قائمة الخدمات.")
            return

        service = state['service']
        collected_params = state['collected_params']

        bot.send_message(user_id, f"جاري تقديم طلبك لخدمة '{service['name']}'...")

        # The service object from get_all_data now lacks the base_url.
        # This is a flaw in my plan. The bot needs to know which API config to use.
        # I will fetch it here.
        # This is inefficient, the service query should join the api_config.
        # I will assume the join is not possible and do a separate query.
        # Let's re-read db.py. I did add it to the query. Good.
        base_url = service.get('api_configs', {}).get('base_url')
        if not base_url:
            bot.send_message(user_id, "❌ خطأ فادح: لم يتم العثور على رابط API لهذه الخدمة.")
            return

        api_client = APIClient(base_url=base_url)
        response = api_client.new_order(service['api_service_id'], collected_params)

        if response and response.get('order_id'):
            order_id = response.get('order_id', 'N/A')
            db.add_order(user_id, service['id'], order_id, 'Completed')
            bot.send_message(user_id, f"✅ تم إنشاء طلبك بنجاح!\nرقم الطلب: {order_id}")
            if ADMIN_ID:
                user = message.from_user
                contact_url = f"t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
                params_str = "\n".join([f"- {k}: {v}" for k, v in collected_params.items()])
                admin_message = (
                    f"🎉 طلب جديد ناجح! 🎉\n\n"
                    f"الخدمة: {service['name']}\n"
                    f"المعلمات:\n{params_str}\n"
                    f"مقدم الطلب: {user.first_name} (@{user.username or 'N/A'})\n"
                    f"معرف الطلب: {order_id}"
                )
                keyboard = InlineKeyboardMarkup()
                contact_button = InlineKeyboardButton("تواصل مع المستخدم", url=contact_url)
                keyboard.add(contact_button)
                bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard)
        else:
            error_message = str(response).lower()
            if "insufficient funds" in error_message:
                if ADMIN_ID:
                    user = message.from_user
                    params_str = "\n".join([f"- {k}: {v}" for k, v in collected_params.items()])
                    admin_message = (
                        f"⚠️ فشل طلب بسبب عدم كفاية الرصيد ⚠️\n\n"
                        f"الخدمة: {service['name']}\n"
                        f"المعلمات:\n{params_str}\n"
                        f"مقدم الطلب: {user.first_name} (@{user.username or 'N/A'})\n"
                        f"الرجاء معالجة الطلب يدويًا."
                    )
                    bot.send_message(ADMIN_ID, admin_message)
                bot.send_message(user_id, "⏳ فشل طلبك ولكن تم إرساله للمسؤول.")
            else:
                bot.send_message(user_id, f"❌ حدث خطأ أثناء إنشاء الطلب.\nالاستجابة: `{response}`")

        if user_id in user_state:
            del user_state[user_id]

    @bot.callback_query_handler(func=lambda call: call.data.startswith('service:'))
    def handle_service_selection(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        service_id = int(call.data.split(':')[1])

        all_services = db.get_all_data().get('services', [])
        service = next((s for s in all_services if s['id'] == service_id), None)

        if not service:
            bot.send_message(call.message.chat.id, "لم يتم العثور على الخدمة.")
            return

        # Start the process
        params_to_ask = json.loads(service.get('params')) if service.get('params') else []
        if not params_to_ask:
            bot.send_message(call.message.chat.id, "لا توجد معلمات مطلوبة لهذه الخدمة، لا يمكن إكمال الطلب.")
            return

        user_state[user_id] = {
            'service': service,
            'params_to_ask': list(params_to_ask),
            'collected_params': {}
        }

        # Edit the previous message to show the description and start button
        description = service.get('description', 'لا يوجد وصف متاح.')
        text = f"<b>{service['name']}</b>\n\n{description}"
        keyboard = InlineKeyboardMarkup()
        order_button = InlineKeyboardButton("📝 طلب الخدمة الآن", callback_data=f"start_order_flow")
        keyboard.add(order_button)
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard, parse_mode='HTML')

    @bot.callback_query_handler(func=lambda call: call.data == 'start_order_flow')
    def handle_order_start_callback(call):
        bot.answer_callback_query(call.id)
        # Delete the description message and start asking questions
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        ask_next_param(call.message)
