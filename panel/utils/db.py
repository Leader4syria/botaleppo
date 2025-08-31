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

def add_service(name, category_id, description, api_service_id):
    try:
        response = supabase.table('services').insert({
            'name': name,
            'category_id': category_id,
            'description': description,
            'api_service_id': api_service_id
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error adding service: {e}")
        return None

def update_service(id, name, category_id, description, api_service_id):
    try:
        response = supabase.table('services').update({
            'name': name,
            'category_id': category_id,
            'description': description,
            'api_service_id': api_service_id
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

# --- API Configs ---

def get_api_configs():
    try:
        response = supabase.table('api_configs').select('*').order('id').execute()
        return response.data
    except Exception as e:
        print(f"Error fetching API configs: {e}")
        return []

def get_api_config(id):
    try:
        response = supabase.table('api_configs').select('*').eq('id', id).single().execute()
        return response.data
    except Exception as e:
        print(f"Error fetching API config: {e}")
        return None

def add_api_config(api_name, base_url, auth_header_name, auth_token):
    try:
        response = supabase.table('api_configs').insert({
            'api_name': api_name,
            'base_url': base_url,
            'auth_header_name': auth_header_name,
            'auth_token': auth_token
        }).execute()
        return response.data
    except Exception as e:
        print(f"Error adding API config: {e}")
        return None

def update_api_config(id, api_name, base_url, auth_header_name, auth_token):
    try:
        response = supabase.table('api_configs').update({
            'api_name': api_name,
            'base_url': base_url,
            'auth_header_name': auth_header_name,
            'auth_token': auth_token
        }).eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error updating API config: {e}")
        return None

def delete_api_config(id):
    try:
        response = supabase.table('api_configs').delete().eq('id', id).execute()
        return response.data
    except Exception as e:
        print(f"Error deleting API config: {e}")
        return None
