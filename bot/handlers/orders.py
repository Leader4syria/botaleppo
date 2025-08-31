from bot.utils.api import APIClient
from bot.utils import db
from bot.config import ADMIN_ID
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

def register_handlers(bot):
    # This dictionary will temporarily store user conversation state
    user_state = {}

    def start_ordering_process(call):
        user_id = call.from_user.id
        service_id = int(call.data.split(':')[1])

        all_services = db.get_all_data().get('services', [])
        service = next((s for s in all_services if s['id'] == service_id), None)

        if not service:
            bot.answer_callback_query(call.id, "Service not found.")
            return

        # Safely load params
        try:
            params_to_ask = json.loads(service.get('params')) if service.get('params') else []
        except (json.JSONDecodeError, TypeError):
            params_to_ask = []

        # If there are no params, we can't proceed with this logic.
        # We can either order directly or inform the user. Let's inform.
        if not params_to_ask:
            bot.answer_callback_query(call.id, "لا توجد معلمات مطلوبة لهذه الخدمة، لا يمكن إكمال الطلب.", show_alert=True)
            return

        user_state[user_id] = {
            'service': service,
            'params_to_ask': list(params_to_ask), # Make a copy
            'collected_params': {}
        }

        ask_next_param(call.message)

    def ask_next_param(message):
        user_id = message.chat.id # In next_step_handler, it's chat.id
        state = user_state.get(user_id)

        if not state or not state['params_to_ask']:
            # We are done, finalize the order
            finalize_order(message)
            return

        next_param_name = state['params_to_ask'][0]
        msg = bot.send_message(user_id, f"الرجاء إدخال '{next_param_name}':")
        bot.register_next_step_handler(msg, process_next_param)

    def process_next_param(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state:
            bot.send_message(user_id, "حدث خطأ، يرجى المحاولة من جديد.")
            return

        param_name = state['params_to_ask'].pop(0)
        state['collected_params'][param_name] = message.text

        ask_next_param(message)

    def finalize_order(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state:
            bot.send_message(user_id, "حدث خطأ، يرجى المحاولة من جديد.")
            return

        service = state['service']
        collected_params = state['collected_params']

        bot.send_message(user_id, f"جاري تقديم طلبك لخدمة '{service['name']}'...")

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

            # Admin notification for success
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
        start_ordering_process(call)
