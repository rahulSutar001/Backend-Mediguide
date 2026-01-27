import requests
from app.core.config import settings


def upload_to_supabase_storage(
    bucket: str,
    path: str,
    file_bytes: bytes,
    content_type: str = "image/png",
):
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{path}"

    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": content_type,
        "x-upsert": "true",
    }

    response = requests.post(url, headers=headers, data=file_bytes)

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Storage upload failed: {response.status_code} - {response.text}"
        )

    return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{path}"
