"""
Supabase client initialization
"""
from supabase import create_client, Client
from app.core.config import settings


def get_supabase() -> Client:
    """Get Supabase client instance (anon key, respects RLS)"""
    supabase_url = settings.SUPABASE_URL.rstrip('/') + '/'
    return create_client(
        supabase_url,
        settings.SUPABASE_ANON_KEY
    )


def get_supabase_admin() -> Client:
    """Get Supabase admin client (service role, bypasses RLS) - USE SPARINGLY"""
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
    
    supabase_url = settings.SUPABASE_URL.rstrip('/') + '/'
    return create_client(
        supabase_url,
        settings.SUPABASE_SERVICE_ROLE_KEY
    )
