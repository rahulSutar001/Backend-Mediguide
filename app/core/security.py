"""
Security utilities for JWT verification and Supabase access
"""

from typing import Optional
from fastapi import HTTPException, status, Header, Request, Depends
from supabase import create_client, Client
from supabase import create_client
from app.core.config import settings
import jwt


# -----------------------------
# Supabase Client Helpers
# -----------------------------

def get_supabase_client(use_service_role: bool = False) -> Client:
    """
    Returns a basic Supabase client.
    Does NOT attach user JWT (RLS will NOT work with this alone).
    """
    if use_service_role:
        return create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY
        )

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_ANON_KEY
    )


def get_authed_supabase_client(
    request: Request,
    use_service_role: bool = False
) -> Client:
    """
    Returns a Supabase client authenticated with the user's JWT.
    REQUIRED for RLS-protected table access.
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format"
        )

    supabase = get_supabase_client(use_service_role=use_service_role)

    # 🔥 THIS IS THE CRITICAL LINE (FIXES YOUR ISSUE)
    supabase.postgrest.auth(token)


    return supabase

def get_service_supabase_client():
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_ROLE_KEY,
    )


# -----------------------------
# JWT Verification
# -----------------------------

async def verify_jwt_token(token: str) -> dict:
    """
    Verify Supabase JWT token and return user info
    """
    try:
        supabase = get_supabase_client()

        # Safest verification method
        response = supabase.auth.get_user(token)

        if not response.user:
            print("[AUTH DEBUG] Supabase rejected token (no user returned)")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

        # Optional: Print decoded for verification of audience
        decoded = jwt.decode(
            token,
            options={"verify_signature": False}
        )
        print(f"[AUTH DEBUG] Token Decoded: {decoded}")

        return {
            "user_id": decoded.get("sub"),
            "email": decoded.get("email"),
            "role": decoded.get("role", "authenticated")
        }

    except Exception as e:
        print(f"[AUTH DEBUG] Token verification failed: {str(e)}")
        # Print Supabase URL to confirm environment
        print(f"[AUTH DEBUG] Checking against Supabase URL: {settings.SUPABASE_URL}")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}"
        )


# -----------------------------
# FastAPI Dependency
# -----------------------------

async def get_current_user(
    authorization: Optional[str] = Header(None)
) -> dict:
    """
    FastAPI dependency to extract and verify the current user
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    # Safe, case-insensitive token extraction
    import re
    token = re.sub(r"^bearer\s+", "", authorization, flags=re.IGNORECASE).strip()

    return await verify_jwt_token(token)


# Admin-specific emails allowed to access admin routes
ADMIN_EMAILS = [
    "rahulsutar977@gmail.com",
    "rahul@example.com",
    "sutarrahul709@gmail.com" # Example placeholder
]

async def get_admin_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    FastAPI dependency to verify if current user is an admin
    """
    if current_user.get("email") not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user
