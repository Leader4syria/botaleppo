from bot.utils.supabase_client import supabase

def get_all_data():
    try:
        categories = supabase.table('categories').select('*').execute().data
        services = supabase.table('services').select('*, api_configs(base_url), params, qty_values, price, available').execute().data
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

def add_order(user_id, service_id, external_order_id, status='pending', params=None):
    try:
        order_data = {
            'user_id': user_id,
            'service_id': service_id,
            'external_order_id': external_order_id,
            'status': status,
        }
        if params:
            order_data['params'] = params

        # Fire-and-forget insert. We assume success if no exception is raised.
        supabase.table('orders').insert(order_data).execute()
        return True
    except Exception as e:
        print(f"ERROR: Failed to add order to DB for user {user_id}. Reason: {e}")
        return False

def deduct_balance_from_user(user_id, amount_to_deduct):
    try:
        # This function calls a Supabase RPC function to decrement the user's balance.
        response = supabase.rpc('decrement_balance', {
            'user_id_in': user_id,
            'amount_in': amount_to_deduct
        }).execute()
        return response.data
    except Exception as e:
        print(f"ERROR: Exception during balance deduction for User ID {user_id}: {e}")
        return None

def get_orders_for_user(user_id):
    try:
        # Fetching order and the related service name
        response = supabase.table('orders').select('*, services(name)').eq('user_id', user_id).order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching orders for user: {e}")
        return []
