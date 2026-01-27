-- Create Supabase Storage bucket for medical reports
-- Run this in Supabase SQL Editor

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
