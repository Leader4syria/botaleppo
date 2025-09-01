from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_keyboard(items, item_type, back_callback_data=None):
    keyboard = InlineKeyboardMarkup(row_width=1)
    buttons = []
    for item in items:
        # Check if the item is a service and has the required fields
        if item_type == 'service':
            price = item.get('price', 0.0)
            available = item.get('available', False)
            availability_emoji = "✅" if available else "❌"
            button_text = f"{item['name']} | {price:.2f} {availability_emoji}"
        else:
            button_text = item['name']

        buttons.append(InlineKeyboardButton(button_text, callback_data=f"{item_type}:{item['id']}"))

    keyboard.add(*buttons)

    if back_callback_data:
        keyboard.add(InlineKeyboardButton("⬅️ رجوع", callback_data=back_callback_data))

    return keyboard

def main_menu_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    services_btn = InlineKeyboardButton("🛍️ الخدمات", callback_data="menu:services")
    my_info_btn = InlineKeyboardButton("ℹ️ معلوماتي", callback_data="menu:my_info")
    my_orders_btn = InlineKeyboardButton("📦 طلباتي", callback_data="menu:my_orders")
    contact_us_btn = InlineKeyboardButton("📞 تواصل معنا", callback_data="menu:contact_us")
    keyboard.add(services_btn)
    keyboard.add(my_info_btn, my_orders_btn)
    keyboard.add(contact_us_btn)
    return keyboard
