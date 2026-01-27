import sys
import os
sys.path.append(os.getcwd())

from app.core.config import settings
from app.core.security import get_service_supabase_client

print(f"SUPABASE_URL from settings: '{settings.SUPABASE_URL}'")

try:
    client = get_service_supabase_client()
    print("Supabase client created successfully.")
    
    # Inspect client internal URLs
    print(f"Client supabase_url: {getattr(client, 'supabase_url', 'N/A')}")
    print(f"Client storage_url: {getattr(client, 'storage_url', 'N/A')}")
    
    if hasattr(client, 'storage'):
        # Checking likely attributes for storage client URL
        print(f"Storage client _url: {getattr(client.storage, '_url', 'N/A')}")
        print(f"Storage client url: {getattr(client.storage, 'url', 'N/A')}")
except Exception as e:
    print(f"Error creating client: {e}")
