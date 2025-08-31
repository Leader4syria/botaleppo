from functools import wraps
from bot.config import CHANNEL_USERNAME

def check_subscription(bot):
    def decorator(func):
        @wraps(func)
        def wrapper(message_or_call):
            user_id = message_or_call.from_user.id

            # Allow admin to bypass check
            from bot.config import ADMIN_ID
            if str(user_id) == ADMIN_ID:
                return func(message_or_call)

            try:
                member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
                if member.status not in ['creator', 'administrator', 'member']:
                    raise Exception("User is not a member.")
            except Exception:
                text = (
                    f"عذراً، يجب عليك الاشتراك في القناة أولاً لاستخدام البوت.\n\n"
                    f"رابط القناة: {CHANNEL_USERNAME}\n\n"
                    f"بعد الاشتراك، اضغط على /start مرة أخرى."
                )
                if hasattr(message_or_call, 'message'): # It's a callback query
                    chat_id = message_or_call.message.chat.id
                    try:
                        bot.send_message(chat_id, text)
                        bot.answer_callback_query(message_or_call.id)
                    except Exception as e:
                        print(f"Error handling callback for non-member: {e}")
                else: # It's a message
                    bot.reply_to(message_or_call, text)
                return

            return func(message_or_call)
        return wrapper
    return decorator
