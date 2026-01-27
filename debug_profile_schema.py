import asyncio
from app.core.security import get_service_supabase_client
from app.supabase.client import get_supabase

async def main():
    print("Initializing Supabase Client...")
    # Try service role first
    try:
        supabase = get_service_supabase_client()
        print("Service Role Client initialized.")
    except Exception as e:
        print(f"Failed to init service role: {e}")
        return

    print("Fetching one profile...")
    try:
        # fetch 1 row
        response = supabase.table("profiles").select("*").limit(1).execute()
        if response.data:
            print("--- KEYS ---")
            for k in response.data[0].keys():
                print(f"KEY: {k}")
            print("--- END KEYS ---")
        else:
            print("No profiles found.")
    except Exception as e:
        print(f"Error fetching profiles: {e}")

if __name__ == "__main__":
    asyncio.run(main())
