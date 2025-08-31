from bot.utils.supabase_client import supabase

def get_all_data():
    try:
        categories = supabase.table('categories').select('*').execute().data
        services = supabase.table('services').select('*').execute().data
        return {"categories": categories, "services": services}
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return {"categories": [], "services": []}

def get_user(user_id):
    try:
        response = supabase.table('users').select('*').eq('id', user_id).single().execute()
        return response.data
    except Exception:
        return None

def add_user(user_id, first_name, username):
    try:
        response = supabase.table('users').insert({
            'id': user_id,
            'first_name': first_name,
            'username': username
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error adding user: {e}")
        return None

def add_order(user_id, service_id, external_order_id, status='pending'):
    try:
        response = supabase.table('orders').insert({
            'user_id': user_id,
            'service_id': service_id,
            'external_order_id': external_order_id,
            'status': status
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error adding order: {e}")
        return None

def get_orders_for_user(user_id):
    try:
        # Fetching order and the related service name
        response = supabase.table('orders').select('*, services(name)').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching orders for user: {e}")
        return []
