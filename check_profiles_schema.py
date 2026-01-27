import asyncio
import os
# from dotenv import load_dotenv - removing dependency
from supabase import create_client

# Manual .env loading
def load_env():
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
    except Exception as e:
        print(f"Warning: could not load .env: {e}")

load_env()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Error: Missing credentials")
    exit(1)

supabase = create_client(url, key)

async def check_schema():
    print("Checking 'profiles' table columns...")
    try:
        # Fetch one row to see structure
        res = supabase.table("profiles").select("*").limit(1).execute()
        if res.data:
            print("Columns found in first row:", list(res.data[0].keys()))
            print("Sample row:", res.data[0])
        else:
            print("No profiles found to inspect.")
            
        # Check if email search works
        print("\nChecking email search...")
        # Try to find a user with a common domain or just any user
        if res.data:
            test_id = res.data[0].get("id")
            # Try to get user from auth to see their email
            user_res = supabase.auth.admin.get_user_by_id(test_id)
            if user_res.user:
                email = user_res.user.email
                print(f"Testing search for email: {email}")
                
                search_res = supabase.table("profiles").select("id").eq("email", email).execute()
                print(f"Search result: {search_res.data}")
                if not search_res.data:
                    print("❌ Search failed! 'email' column likely missing or empty in profiles.")
                else:
                    print("✅ Search successful.")
            else:
                print("Could not fetch auth user details.")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_schema())
