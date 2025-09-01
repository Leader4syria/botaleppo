def send_status_update(bot, user_id, order_id, new_status):
    """
    Sends a message to a user about their order status update.
    """
    status_map = {
        'in_progress': 'قيد التنفيذ',
        'completed': 'مكتمل',
        'canceled': 'ملغى',
        'pending': 'قيد الانتظار'
    }
    status_text = status_map.get(new_status, new_status)

    message = f"🔔 تحديث حالة الطلب!\n\nتم تحديث حالة طلبك رقم `{order_id}` إلى: **{status_text}**"
    try:
        bot.send_message(user_id, message, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to send status update to user {user_id}: {e}")

def send_balance_update(bot, user_id, amount_added, new_balance):
    """
    Sends a message to a user about a balance update.
    """
    message = f"💰 تم تحديث رصيدك!\n\nتمت إضافة `{amount_added}` إلى حسابك.\nرصيدك الجديد هو: **{new_balance:.2f}**"
    try:
        bot.send_message(user_id, message, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to send balance update to user {user_id}: {e}")
