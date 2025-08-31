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

def add_service(name, category_id, description, api_service_id, api_config_id):
    try:
        response = supabase.table('services').insert({
            'name': name,
            'category_id': category_id,
            'description': description,
            'api_service_id': api_service_id,
            'api_config_id': api_config_id
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

# No longer needed
