from bot.keyboards.inline import generate_keyboard
from bot.utils import db
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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


def format_categories_recursive(categories, services, parent_id, depth=0):
    """Recursively build a formatted string of categories and their services."""
    output = ""
    indent = "  " * depth  # Two spaces per depth level

    child_categories = find_children_categories(categories, parent_id)
    for category in child_categories:
        output += f"{indent}📁 **{category['name']}**\n"

        # List services in this category
        service_indent = indent + "  "
        category_services = find_services_in_category(services, category['id'])
        for service in category_services:
            # Note: The user can't click these, so we show the ID for manual ordering if needed.
            availability_emoji = "✅" if service.get('available', True) else "❌"
            output += f"{service_indent}➖ {service['name']} (ID: {service['id']}) {availability_emoji}\n"

        # Recursive call for sub-categories
        output += format_categories_recursive(categories, services, category['id'], depth + 1)

    return output

def show_all_services_formatted(bot, message):
    """Fetch all data and display it in a single formatted message."""
    data = db.get_all_data()
    categories = data.get('categories', [])
    services = data.get('services', [])

    text = "📋 **جميع الخدمات والتصنيفات**\n\n"
    formatted_list = format_categories_recursive(categories, services, None)

    if not formatted_list:
        text += "عذراً، لا توجد أي خدمات أو تصنيفات معرفة حالياً."
    else:
        text += formatted_list

    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⬅️ رجوع إلى القائمة الرئيسية", callback_data="menu:back_to_main"))

    # Telegram has a message length limit of 4096 characters.
    # If the message is too long, we need to truncate it.
    if len(text) > 4096:
        text = text[:4090] + "\n\n..."

    bot.edit_message_text(text, chat_id=message.chat.id, message_id=message.message_id, reply_markup=keyboard, parse_mode='Markdown')


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
