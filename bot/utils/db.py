from bot.utils.supabase_client import supabase

def get_all_data():
    try:
        categories = supabase.table('categories').select('*').execute().data
        services = supabase.table('services').select('*').execute().data
        return {"categories": categories, "services": services}
    except Exception as e:
        print(f"Error fetching data from Supabase: {e}")
        return {"categories": [], "services": []}
