from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_keyboard(items, item_type, back_callback_data=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    buttons = [InlineKeyboardButton(item['name'], callback_data=f"{item_type}:{item['id']}") for item in items]
    keyboard.add(*buttons)

    if back_callback_data:
        keyboard.add(InlineKeyboardButton("⬅️ رجوع", callback_data=back_callback_data))

    return keyboard
