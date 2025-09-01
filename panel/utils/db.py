from panel.utils.supabase_client import supabase

def get_categories():
    try:
        response = supabase.table('categories').select('*').order('id').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []

def get_category(id):
    try:
        response = supabase.table('categories').select('*').eq('id', id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching category: {e}")
        return None

def add_category(name, parent_id=None):
    try:
        response = supabase.table('categories').insert({'name': name, 'parent_id': parent_id}).execute()
        return response.data
    except Exception as e:
        print(f"Error adding category: {e}")
        return None

def update_category(id, name, parent_id=None):
    try:
        response = supabase.table('categories').update({'name': name, 'parent_id': parent_id}).eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating category: {e}")
        return None

def delete_category(id):
    try:
        response = supabase.table('categories').delete().eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting category: {e}")
        return None

def get_services():
    try:
        response = supabase.table('services').select('*, categories(*)').order('id').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching services: {e}")
        return []

def get_service(id):
    try:
        response = supabase.table('services').select('*').eq('id', id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching service: {e}")
        return None

def add_service(name, category_id, description, api_service_id, api_config_id, price, params, qty_values, available):
    try:
        response = supabase.table('services').insert({
            'name': name,
            'category_id': category_id,
            'description': description,
            'api_service_id': api_service_id,
            'api_config_id': api_config_id,
            'price': price,
            'params': params,
            'qty_values': qty_values,
            'available': available
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error adding service: {e}")
        return None

def update_service(id, name, category_id, description, api_service_id, api_config_id):
    try:
        response = supabase.table('services').update({
            'name': name,
            'category_id': category_id,
            'description': description,
            'api_service_id': api_service_id,
            'api_config_id': api_config_id
        }).eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating service: {e}")
        return None

def delete_service(id):
    try:
        response = supabase.table('services').delete().eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting service: {e}")
        return None

def get_users():
    try:
        response = supabase.table('users').select('*').order('id').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching users: {e}")
        return []

def add_balance_to_user(user_id, amount_to_add):
    try:
        response = supabase.rpc('increment_balance', {
            'user_id_in': user_id,
            'amount_in': amount_to_add
        }).execute()
        # The RPC function now returns the new balance directly
        return response.data
    except Exception as e:
        print(f"Error adding balance: {e}")
        return None

def deduct_balance_from_user(user_id, amount_to_deduct):
    try:
        response = supabase.rpc('decrement_balance', {
            'user_id_in': user_id,
            'amount_in': amount_to_deduct
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error deducting balance: {e}")
        return None

# --- Order Management ---

def get_all_orders():
    try:
        response = supabase.table('orders').select('*, services(name), users(first_name, username)').order('created_at', desc=True).execute()
        return response.data
    except Exception as e:
        print(f"Error fetching all orders: {e}")
        return []

def get_order(order_id):
    try:
        response = supabase.table('orders').select('user_id').eq('id', order_id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching order: {e}")
        return None

def update_order_status(order_id, new_status):
    try:
        response = supabase.table('orders').update({'status': new_status}).eq('id', order_id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating order status: {e}")
        return None
