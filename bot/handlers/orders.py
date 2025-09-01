from bot.utils.api import APIClient
from bot.utils import db
from bot.config import ADMIN_ID, ORANOS_API_URL
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

        # Check for quantity validation (assuming param name is 'qty')
        if param_name.lower() == 'qty':
            qty_rules = state['service'].get('qty_values')
            if qty_rules and isinstance(qty_rules, dict):
                min_qty = qty_rules.get('min')
                max_qty = qty_rules.get('max')
                if min_qty is not None and max_qty is not None:
                    question += f"\n(الكمية المسموح بها: بين {min_qty} و {max_qty})"

        msg = bot.send_message(user_id, question)
        bot.register_next_step_handler(msg, process_next_param)

    def process_next_param(message):
        user_id = message.chat.id
        state = user_state.get(user_id)

        if not state or not state.get('service'):
            bot.send_message(user_id, "حدث خطأ أو انتهت مهلة الجلسة. يرجى إعادة بدء الطلب من قائمة الخدمات.")
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

        state['collected_params'][param_name] = message.text
        state['params_to_ask'].pop(0)
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

        # If service has no api_service_id, it's a manual order.
        if service.get('api_service_id') is None:
            params_json = json.dumps(collected_params, ensure_ascii=False)
            order_id = db.add_order(user_id, service['id'], None, 'Pending', params=params_json)

            if order_id:
                service_price = service.get('price', 0.0)
                print(f"DEBUG: Attempting to deduct balance for MANUAL order. User ID: {user_id}, Amount: {service_price}")
                db.deduct_balance_from_user(user_id, float(service_price))
                bot.send_message(user_id, f"✅ تم استلام طلبك بنجاح!\nسيتم معالجته يدويًا من قبل المسؤول.\nرقم الطلب للمراجعة: {order_id}")

                if ADMIN_ID:
                    user = message.from_user
                    contact_url = f"t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
                    params_str = "\n".join([f"- {k}: {v}" for k, v in collected_params.items()])
                    admin_message = (
                        f"📝 طلب خدمة يدوية (مع معلمات) 📝\n\n"
                        f"الخدمة: {service['name']}\n"
                        f"رقم الطلب: {order_id}\n"
                        f"المعلمات:\n{params_str}\n"
                        f"مقدم الطلب: {user.first_name} (@{user.username or 'N/A'})"
                    )
                    keyboard = InlineKeyboardMarkup()
                    contact_button = InlineKeyboardButton("تواصل مع المستخدم", url=contact_url)
                    keyboard.add(contact_button)
                    bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard)
            else:
                bot.send_message(user_id, "حدث خطأ أثناء إنشاء طلبك اليدوي. يرجى المحاولة مرة أخرى أو التواصل مع الإدارة.")

        else: # This is an API order
            if not ORANOS_API_URL:
                bot.send_message(user_id, "خطأ في الإعدادات: رابط الـ API غير محدد. تم إبلاغ المسؤول.")
                print("CRITICAL: ORANOS_API_URL is not set.")
                # Optionally notify admin
                return

            api_client = APIClient(base_url=ORANOS_API_URL)
            response = api_client.new_order(service['api_service_id'], collected_params)

            if response and response.get('order_id'):
                external_order_id = response.get('order_id', 'N/A')

                service_price = service.get('price', 0.0)
                print(f"DEBUG: Attempting to deduct balance for API order. User ID: {user_id}, Amount: {service_price}")
                db.deduct_balance_from_user(user_id, float(service_price))
                db.add_order(user_id, service['id'], external_order_id, 'Completed')

                bot.send_message(user_id, f"✅ تم إنشاء طلبك بنجاح!\nرقم الطلب: {external_order_id}")

                if ADMIN_ID:
                    user = message.from_user
                    contact_url = f"t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
                    params_str = "\n".join([f"- {k}: {v}" for k, v in collected_params.items()])
                    admin_message = (
                        f"🎉 طلب جديد ناجح! 🎉\n\n"
                        f"الخدمة: {service['name']}\n"
                        f"المعلمات:\n{params_str}\n"
                        f"مقدم الطلب: {user.first_name} (@{user.username or 'N/A'})\n"
                        f"معرف الطلب: {external_order_id}"
                    )
                    keyboard = InlineKeyboardMarkup()
                    contact_button = InlineKeyboardButton("تواصل مع المستخدم", url=contact_url)
                    keyboard.add(contact_button)
                    bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard)
            else:
                if ADMIN_ID:
                    user = message.from_user
                    params_str = "\n".join([f"- {k}: {v}" for k, v in collected_params.items()])
                    admin_message = (
                        f"⚠️ فشل طلب تلقائي ⚠️\n\n"
                        f"الخدمة: {service['name']}\n"
                        f"المعلمات:\n{params_str}\n"
                        f"مقدم الطلب: {user.first_name} (@{user.username or 'N/A'})\n"
                        f"استجابة الـ API: `{response}`\n\n"
                        f"الرجاء معالجة الطلب يدويًا."
                    )
                    bot.send_message(ADMIN_ID, admin_message, parse_mode='Markdown')
                bot.send_message(user_id, "⏳ حدث خطأ أثناء معالجة طلبك. تم إرسال التفاصيل إلى المسؤول لمتابعة الطلب يدويًا.")

        if user_id in user_state:
            del user_state[user_id]

    @bot.callback_query_handler(func=lambda call: call.data.startswith('service:'))
    def handle_service_selection(call):
        user_id = call.from_user.id
        service_id = int(call.data.split(':')[1])

        all_services = db.get_all_data().get('services', [])
        service = next((s for s in all_services if s['id'] == service_id), None)

        if not service:
            bot.answer_callback_query(call.id, "لم يتم العثور على الخدمة.", show_alert=True)
            return

        user = db.get_user(user_id)
        user_balance = user.get('balance', 0.0) if user else 0.0
        service_price = service.get('price', float('inf'))

        if float(user_balance) < float(service_price):
            bot.answer_callback_query(call.id, f"رصيدك الحالي ({user_balance:.2f}) غير كافٍ. سعر هذه الخدمة هو {service_price:.2f}.", show_alert=True)
            return

        bot.answer_callback_query(call.id)

        try:
            params_to_ask = json.loads(service.get('params')) if service.get('params') else []
        except (json.JSONDecodeError, TypeError):
            params_to_ask = []

        # If no params, we can't use the dynamic flow. This is for manually added services.
        if not params_to_ask and service.get('api_service_id') is None:
            # Manually added service, just notify admin
            if ADMIN_ID:
                user = call.from_user
                admin_message = (
                    f"📝 طلب خدمة يدوية 📝\n\n"
                    f"الخدمة: {service['name']}\n"
                    f"المستخدم: {user.first_name} (@{user.username or 'N/A'})\n"
                    f"ID: `{user.id}`\n\n"
                    f"يرجى التواصل مع المستخدم لإكمال الطلب."
                )
                contact_url = f"t.me/{user.username}" if user.username else f"tg://user?id={user.id}"
                keyboard = InlineKeyboardMarkup()
                contact_button = InlineKeyboardButton("تواصل مع المستخدم", url=contact_url)
                keyboard.add(contact_button)
                bot.send_message(ADMIN_ID, admin_message, reply_markup=keyboard, parse_mode='Markdown')
            bot.edit_message_text("تم إرسال طلبك لهذه الخدمة إلى المسؤول وسيتواصل معك لإكماله.", chat_id=call.message.chat.id, message_id=call.message.message_id)
            return

        user_state[user_id] = {
            'service': service,
            'params_to_ask': list(params_to_ask),
            'collected_params': {}
        }

        description = service.get('description', 'لا يوجد وصف متاح.')
        price_str = f"السعر: {service.get('price', 'N/A')}"
        text = f"<b>{service['name']}</b>\n\n{description}\n\n{price_str}"
        keyboard = InlineKeyboardMarkup()
        order_button = InlineKeyboardButton("📝 طلب الخدمة الآن", callback_data=f"start_order_flow")
        keyboard.add(order_button)
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=keyboard, parse_mode='HTML')

    @bot.callback_query_handler(func=lambda call: call.data == 'start_order_flow')
    def handle_order_start_callback(call):
        bot.answer_callback_query(call.id)
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        ask_next_param(call.message)
