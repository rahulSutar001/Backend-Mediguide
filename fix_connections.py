import asyncio
from app.core.config import settings
from app.supabase.client import get_supabase
from app.core.security import get_service_supabase_client

async def fix_bad_connections():
    print("--- Starting Connection Audit ---")
    admin_supabase = get_service_supabase_client()
    
    # 1. Fetch all connections
    res = admin_supabase.table("family_connections").select("*").execute()
    connections = res.data or []
    print(f"Found {len(connections)} total connections.")
    
    for conn in connections:
        conn_id = conn["id"]
        user_id = conn["user_id"] # Sender
        connected_user_id = conn["connected_user_id"] # Receiver
        sender_display_name = conn.get("sender_display_name")
        receiver_display_name = conn.get("receiver_display_name")
        
        # Fetch SENDER profile to compare name
        s_res = admin_supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        sender_profile = s_res.data
        if not sender_profile:
            continue
            
        sender_actual_name = sender_profile.get("full_name") or sender_profile.get("profile_name")
        
        print(f"\nChecking Connection {conn_id}...")
        print(f"  Sender: {sender_actual_name} ({user_id})")
        print(f"  Target: {connected_user_id}")
        print(f"  Saved Sender Display Name: '{sender_display_name}'")
        print(f"  Saved Receiver Display Name: '{receiver_display_name}'")
        
        # DETECT THE BUG PATTERN
        # Logic Bug: sender_display_name was set to Sender's Name.
        # receiver_display_name was set to None.
        
        bug_found = False
        if sender_display_name == sender_actual_name:
             print("  [!] SUSPICIOUS: Sender sees their own name!")
             bug_found = True
        
        if receiver_display_name is None:
             print("  [!] SUSPICIOUS: Receiver sees NULL (should check if they see Sender Name)")
             # Usually Receiver should see Sender Name. If None, frontend might show "Unknown" or Name Fallback?
             # My fix sets it to Sender Name.
             bug_found = True
             
        if bug_found:
             print("  -> FIXING...")
             
             # CORRECT LOGIC:
             # sender_display_name should be NULL (to fallback to Target's Name) OR 'nickname' (unknown here)
             # receiver_display_name should be SENDER'S NAME.
             
             update_data = {
                 "sender_display_name": None, # Force fallback
                 "receiver_display_name": sender_actual_name
             }
             
             admin_supabase.table("family_connections").update(update_data).eq("id", conn_id).execute()
             print("  -> FIXED.")

if __name__ == "__main__":
    asyncio.run(fix_bad_connections())
