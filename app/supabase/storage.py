"""
Supabase Storage operations for medical report images
"""
from typing import BinaryIO, Optional
from supabase import Client
from app.core.config import settings
from app.supabase.client import get_supabase_admin


async def upload_report_image(
    file: bytes,
    user_id: str,
    report_id: str,
    filename: str
) -> str:
    """
    Upload medical report image to Supabase Storage
    
    Args:
        file: Image data as bytes
        user_id: User ID (for folder organization)
        report_id: Report ID (for filename)
        filename: Original filename
    
    Returns:
        Public URL of uploaded file
    
    Raises:
        Exception: If upload fails
    """
    # Use admin client for storage operations (needs service role)
    supabase = get_supabase_admin()
    
    # Organize files by user: medical-reports/{user_id}/{report_id}.{ext}
    file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
    storage_path = f"{user_id}/{report_id}.{file_extension}"
    
    # Determine content type based on file extension
    content_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'webp': 'image/webp'
    }
    content_type = content_type_map.get(file_extension.lower(), 'image/jpeg')
    
    try:
        # Check if bucket exists, create if not
        try:
            buckets = supabase.storage.list_buckets()
            bucket_names = [b.name for b in buckets]
            if settings.STORAGE_BUCKET not in bucket_names:
                print(f"[WARNING] Bucket '{settings.STORAGE_BUCKET}' not found. Creating...")
                # Try to create bucket (requires service role)
                supabase.storage.create_bucket(
                    settings.STORAGE_BUCKET,
                    options={"public": True}
                )
                print(f"[SUCCESS] Bucket '{settings.STORAGE_BUCKET}' created")
        except Exception as bucket_check_error:
            print(f"[WARNING] Could not check/create bucket: {bucket_check_error}")
            # Continue anyway - might already exist
        
        # Upload to Supabase Storage
        response = supabase.storage.from_(settings.STORAGE_BUCKET).upload(
            path=storage_path,
            file=file,
            file_options={
                "content-type": content_type,
                "upsert": "true"  # Overwrite if exists
            }
        )
        
        # Get public URL
        public_url = supabase.storage.from_(settings.STORAGE_BUCKET).get_public_url(
            storage_path
        )
        
        return public_url
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Storage upload failed: {error_msg}")
        
        # Provide helpful error message
        if "Bucket not found" in error_msg or "404" in error_msg:
            raise Exception(
                f"Storage bucket '{settings.STORAGE_BUCKET}' not found. "
                f"Please create it in Supabase Dashboard → Storage, or run the migration script: "
                f"supabase/migrations/002_create_storage_bucket.sql"
            )
        raise Exception(f"Failed to upload image to storage: {error_msg}")


async def delete_report_image(user_id: str, report_id: str) -> bool:
    """
    Delete medical report image from Supabase Storage
    
    Args:
        user_id: User ID
        report_id: Report ID
    
    Returns:
        True if deleted successfully
    """
    try:
        supabase = get_supabase_admin()
        
        # Try to find and delete the file (may have different extensions)
        extensions = ['jpg', 'jpeg', 'png', 'webp']
        for ext in extensions:
            storage_path = f"{user_id}/{report_id}.{ext}"
            try:
                supabase.storage.from_(settings.STORAGE_BUCKET).remove([storage_path])
                return True
            except:
                continue
        
        return False
    except Exception:
        return False
