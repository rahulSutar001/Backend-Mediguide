-- Add status tracking to report_summaries
-- This enables a deterministic state machine for synthesis generation

DO $$ 
BEGIN 
    -- Add status column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'report_summaries' AND column_name = 'status') THEN
        ALTER TABLE report_summaries ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'completed'; -- Defaulting to completed for existing rows
        ALTER TABLE report_summaries ADD CONSTRAINT check_status CHECK (status IN ('pending', 'completed', 'failed'));
    END IF;

    -- Add error_message column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'report_summaries' AND column_name = 'error_message') THEN
        ALTER TABLE report_summaries ADD COLUMN error_message TEXT;
    END IF;

    -- Add updated_at column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'report_summaries' AND column_name = 'updated_at') THEN
        ALTER TABLE report_summaries ADD COLUMN updated_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Trigger for updated_at
DROP TRIGGER IF EXISTS update_report_summaries_updated_at ON report_summaries;
CREATE TRIGGER update_report_summaries_updated_at BEFORE UPDATE ON report_summaries
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
