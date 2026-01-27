import asyncio
import os
from app.supabase.client import get_supabase

async def check_columns():
    supabase = get_supabase()
    print("Checking family_connections columns...")
    try:
        # Try to select the new columns
        # We limit to 1 row to minimize data
        response = supabase.table("family_connections").select("sender_display_name,receiver_display_name").limit(1).execute()
        print("Columns exist! Query successful.")
        print(response.data)
    except Exception as e:
        print(f"Error selecting columns: {e}")
        print("This confirms the columns are MISSING or NOT ACCESSIBLE.")

if __name__ == "__main__":
    asyncio.run(check_columns())
