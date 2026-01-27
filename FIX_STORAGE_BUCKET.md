# Fix: Storage Bucket Not Found

## Error
```
[ERROR] Storage upload failed: {'statusCode': 404, 'error': Bucket not found, 'message': Bucket not found}
```

## Solution

The `medical-reports` storage bucket doesn't exist in your Supabase project. Create it using one of these methods:

### Method 1: Using Supabase Dashboard (Easiest)

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Go to **Storage** in the left sidebar
4. Click **"New bucket"**
5. Name: `medical-reports`
6. **Public bucket**: ✅ Check this (so images can be accessed)
7. Click **"Create bucket"**

### Method 2: Using SQL (Recommended for Production)

1. Go to Supabase Dashboard → **SQL Editor**
2. Run this SQL:

```sql
-- Create storage bucket (if it doesn't exist)
INSERT INTO storage.buckets (id, name, public)
VALUES ('medical-reports', 'medical-reports', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for medical-reports bucket
CREATE POLICY "Users can upload their own reports"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'medical-reports'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can view their own reports"
ON storage.objects FOR SELECT
USING (
    bucket_id = 'medical-reports'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

CREATE POLICY "Users can delete their own reports"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'medical-reports'
    AND (storage.foldername(name))[1] = auth.uid()::text
);
```

3. Click **"Run"**

### Method 3: Using Migration Script

The migration script is already created at:
`mediguide-backend/supabase/migrations/002_create_storage_bucket.sql`

Copy its contents and run in Supabase SQL Editor.

## Verify

After creating the bucket:

1. Go to Storage in Supabase Dashboard
2. You should see `medical-reports` bucket listed
3. Try uploading a report again

## Additional Notes

- The bucket must be **public** for images to be accessible
- The bucket name must match `STORAGE_BUCKET` in your `.env` file (default: `medical-reports`)
- Storage policies ensure users can only access their own files
