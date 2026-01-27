-- Report Summaries table for caching AI synthesis
-- This table stores one-time generated summaries to avoid repeated OpenAI calls

CREATE TABLE IF NOT EXISTS report_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID REFERENCES reports(id) ON DELETE CASCADE,
    summary_text JSONB, -- Storing the full JSON result from SynthesisService
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(report_id)
);

-- RLS Policies
ALTER TABLE report_summaries ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view summaries of their reports"
    ON report_summaries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM reports
            WHERE reports.id = report_summaries.report_id
            AND reports.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view summaries of connected family reports"
    ON report_summaries FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM reports
            JOIN family_connections ON (
                family_connections.user_id = auth.uid()
                OR family_connections.connected_user_id = auth.uid()
            )
            WHERE reports.id = report_summaries.report_id
            AND family_connections.status = 'connected'
        )
    );

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_report_summaries_report_id ON report_summaries(report_id);
