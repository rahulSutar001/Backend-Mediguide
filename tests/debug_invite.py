import asyncio
import os
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.services.family_service import FamilyService
from app.core.config import settings

async def debug_invite():
    print("--- Starting Family Invite Debug ---")
    
    service = FamilyService()
    
    # 1. Identify a sender (User A)
    # Using 'sutarrahul709@gmail.com' ID from logs
    sender_id = "190bc0b3-1e44-4f2c-a552-28961679734c" 
    
    # 2. Identify a target email (User B)
    # Let's try to find a valid user to invite. 
    # We'll use the service's internal admin client to peek first.
    print("Listing potential targets...")
    users = service.admin_supabase.auth.admin.list_users()
    target_email = None
    
    if isinstance(users, list):
        user_list = users
    elif hasattr(users, "users"):
        user_list = users.users
    else:
        user_list = []
        
    for u in user_list:
        u_email = getattr(u, "email", "") or u.get("email")
        u_id = getattr(u, "id", "") or u.get("id")
        if u_id != sender_id:
            target_email = u_email
            print(f"Found target: {target_email}")
            break
            
    if not target_email:
        print("No other users found to invite!")
        return

    print(f"Attempting to invite {target_email} from {sender_id}...")
    
    try:
        connection_id = await service.send_invite(
            user_id=sender_id,
            email=target_email
        )
        print(f"SUCCESS: Invite sent! Connection ID: {connection_id}")
    except ValueError as ve:
        print(f"EXPECTED ERROR (Caught ValueError): {ve}")
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_invite())
