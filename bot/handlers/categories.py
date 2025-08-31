from bot.keyboards.inline import generate_keyboard
from bot.utils import db

def find_children_categories(categories, parent_id):
    return [cat for cat in categories if cat.get('parent_id') == parent_id]

def find_services_in_category(services, category_id):
    return [srv for srv in services if srv.get('category_id') == category_id]

def find_category(categories, category_id):
    if category_id is None:
        return None
    for cat in categories:
        if cat['id'] == category_id:
            return cat
    return None

def show_main_categories(bot, message):
    data = db.get_all_data()

    text = "اختر فئة:"
    top_level_categories = find_children_categories(data.get('categories', []), None)

    if not top_level_categories:
        text = "عذراً، لا توجد أقسام معرفة حالياً."

    # The back button from the top-level categories should go back to the main menu
    keyboard = generate_keyboard(top_level_categories, 'category', back_callback_data="menu:back_to_main")

    bot.edit_message_text(text, chat_id=message.chat.id, message_id=message.message_id, reply_markup=keyboard)

def register_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith('category:'))
    def handle_category_selection(call):
        data = db.get_all_data()

        category_id_str = call.data.split(':')[1]

        if not category_id_str:
            top_level_categories = find_children_categories(data.get('categories', []), None)
            keyboard = generate_keyboard(top_level_categories, 'category', back_callback_data=None)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="اختر فئة:", reply_markup=keyboard)
            bot.answer_callback_query(call.id)
            return

        category_id = int(category_id_str)

        sub_categories = find_children_categories(data.get('categories', []), category_id)
        services = find_services_in_category(data.get('services', []), category_id)

        current_category = find_category(data.get('categories', []), category_id)
        parent_id = current_category.get('parent_id') if current_category else None

        if parent_id is not None:
            back_callback = f"category:{parent_id}"
        else:
            # If the parent is the root, the back button goes to the main menu
            back_callback = "menu:back_to_main"

        if sub_categories:
            keyboard = generate_keyboard(sub_categories, 'category', back_callback_data=back_callback)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="اختر فئة فرعية:", reply_markup=keyboard)
        elif services:
            keyboard = generate_keyboard(services, 'service', back_callback_data=back_callback)
            bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="اختر خدمة:", reply_markup=keyboard)
        else:
            bot.answer_callback_query(call.id, "لا توجد فئات فرعية أو خدمات هنا.")
