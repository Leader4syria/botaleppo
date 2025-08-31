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
