import sys
import os
sys.path.append(os.getcwd())

import requests

def create_dummy_image():
    with open("test.png", "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82")

create_dummy_image()

# Need an auth token?
# The endpoint requires user_id from token.
# I need to mock the token or obtain one.
# For reproduction of the 500 error which happens *before* or *during* upload, maybe I can use an invalid token and see if it fails with 401 or 500?
# If the 500 happens at ReportService init (Supabase client init), it happens *after* token verification (dependencies).
# But wait, get_service_supabase_client() is called in ReportService.__init__.
# And get_user_id depends on get_current_user.

# I need a valid-looking JWT for get_current_user to pass.
# Or I can try to unit-test ReportService directly without HTTP.

from app.core.config import settings
from app.api.routes.reports import upload_report
from fastapi import Request, UploadFile
from unittest.mock import MagicMock, AsyncMock

# Testing via Python script directly importing service might be easier/faster
# ... but internal dependencies (supabase) need environment.

# Let's try HTTP request first. I need a token.
# If I can't generate a valid token (requires secret), I can't past auth.
# Wait, I have SUPABASE_SERVICE_ROLE_KEY? I can use that to sign a token!
# But app checks SUPABASE_ANON_KEY usually (or user secret).
# Actually, I can use jwt library to sign a token if I have the secret.
# In .env:
# SUPABASE_ANON_KEY=... (This is a JWT itself, not the secret to sign with, usually).
# BUT SUPABASE_ANON_KEY *is* a JWT. The *secret* used to sign it is... usually in Supabase dashboard.
# AND there is `SUPABASE_SERVICE_ROLE_KEY`.

# However, the app verifies using `supabase.auth.get_user(token)`.
# So I need a REAL user token.

# Alternative: Test `ReportService` instantiation in isolation.
# If `ReportService.__init__` triggers the warning (we know it does), does it crash?
# We saw `check_supabase.py` didn't crash.

# Why did the user get 500?
# Maybe `upload_to_supabase_storage` failed?
# If `requests.post` returns 500/400/404 because of the double slash?

# Let's test `upload_to_supabase_storage` in isolation!

from app.supabase.storage_service import upload_to_supabase_storage

print("Testing upload_to_supabase_storage...")
try:
    # Use a dummy bucket/path
    res = upload_to_supabase_storage(
        bucket=settings.STORAGE_BUCKET,
        path="debug_test.png",
        file_bytes=b"fake data",
        content_type="image/png"
    )
    print(f"Success: {res}")
except Exception as e:
    print(f"Failed: {e}")
