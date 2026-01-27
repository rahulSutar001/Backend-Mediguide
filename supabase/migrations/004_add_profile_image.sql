-- Create Supabase Storage bucket for avatars
-- Run this in Supabase SQL Editor

-- 1. Create avatars bucket
INSERT INTO storage.buckets (id, name, public)
VALUES ('avatars', 'avatars', true)
ON CONFLICT (id) DO NOTHING;

-- 2. Add profile_image_url column to profiles table
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'profiles' AND column_name = 'profile_image_url') THEN
        ALTER TABLE profiles ADD COLUMN profile_image_url TEXT;
    END IF;
END $$;

-- 3. Set up Storage Policies for 'avatars'

-- Allow public read access to avatars
DROP POLICY IF EXISTS "Avatar Public Read" ON storage.objects;
CREATE POLICY "Avatar Public Read"
ON storage.objects FOR SELECT
USING ( bucket_id = 'avatars' );

-- Allow authenticated users to upload their own avatar
-- We assume the file path will be '{user_id}/avatar.png' or similar, or just ensuring they are logged in.
-- For stricter security, checks on foldername matching auth.uid() is good practice.
DROP POLICY IF EXISTS "Avatar Auth Upload" ON storage.objects;
CREATE POLICY "Avatar Auth Upload"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'avatars'
    AND auth.role() = 'authenticated'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to update/replace their own avatar
DROP POLICY IF EXISTS "Avatar Auth Update" ON storage.objects;
CREATE POLICY "Avatar Auth Update"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'avatars' 
    AND auth.role() = 'authenticated'
    AND (storage.foldername(name))[1] = auth.uid()::text
);

-- Allow users to delete their own avatar
DROP POLICY IF EXISTS "Avatar Auth Delete" ON storage.objects;
CREATE POLICY "Avatar Auth Delete"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'avatars' 
    AND auth.role() = 'authenticated'
    AND (storage.foldername(name))[1] = auth.uid()::text
);
