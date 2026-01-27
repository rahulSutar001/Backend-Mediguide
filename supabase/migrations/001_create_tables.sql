-- MediGuide Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Reports table
CREATE TABLE IF NOT EXISTS reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    type VARCHAR(100) NOT NULL,
    lab_name VARCHAR(255),
    date DATE,
    status VARCHAR(20) NOT NULL DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    flag_level VARCHAR(10) NOT NULL DEFAULT 'green' CHECK (flag_level IN ('green', 'yellow', 'red')),
    image_url TEXT,
    uploaded_to_abdm BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Report parameters table
CREATE TABLE IF NOT EXISTS report_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    value VARCHAR(100) NOT NULL,
    unit VARCHAR(50),
    normal_range VARCHAR(100),
    flag VARCHAR(10) NOT NULL CHECK (flag IN ('normal', 'high', 'low')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Report explanations table (AI-generated)
CREATE TABLE IF NOT EXISTS report_explanations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parameter_id UUID NOT NULL REFERENCES report_parameters(id) ON DELETE CASCADE,
    what TEXT NOT NULL,
    meaning TEXT NOT NULL,
    causes TEXT[] DEFAULT '{}',
    next_steps TEXT[] DEFAULT '{}',
    generated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Family connections table
CREATE TABLE IF NOT EXISTS family_connections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    connected_user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    invited_email VARCHAR(255),
    nickname VARCHAR(100),
    status VARCHAR(20) NOT NULL DEFAULT 'pending_sent' CHECK (status IN ('pending_sent', 'pending_received', 'connected')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, connected_user_id)
);

-- Chat messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    report_id UUID NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    response TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Subscriptions table
CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'inactive' CHECK (status IN ('active', 'inactive', 'cancelled')),
    tier VARCHAR(20) NOT NULL DEFAULT 'free' CHECK (tier IN ('free', 'premium')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON reports(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_status ON reports(status);
CREATE INDEX IF NOT EXISTS idx_reports_created_at ON reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_report_parameters_report_id ON report_parameters(report_id);
CREATE INDEX IF NOT EXISTS idx_report_explanations_parameter_id ON report_explanations(parameter_id);
CREATE INDEX IF NOT EXISTS idx_family_connections_user_id ON family_connections(user_id);
CREATE INDEX IF NOT EXISTS idx_family_connections_connected_user_id ON family_connections(connected_user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_report_id ON chat_messages(report_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_user_id ON chat_messages(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON subscriptions(user_id);

-- Row Level Security (RLS) Policies

-- Enable RLS on all tables
ALTER TABLE reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_parameters ENABLE ROW LEVEL SECURITY;
ALTER TABLE report_explanations ENABLE ROW LEVEL SECURITY;
ALTER TABLE family_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

-- Reports policies
CREATE POLICY "Users can view their own reports"
    ON reports FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own reports"
    ON reports FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own reports"
    ON reports FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own reports"
    ON reports FOR DELETE
    USING (auth.uid() = user_id);

-- Report parameters policies
CREATE POLICY "Users can view parameters of their reports"
    ON report_parameters FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM reports
            WHERE reports.id = report_parameters.report_id
            AND reports.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can view parameters of connected family reports"
    ON report_parameters FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM reports
            JOIN family_connections ON (
                family_connections.user_id = auth.uid()
                OR family_connections.connected_user_id = auth.uid()
            )
            WHERE reports.id = report_parameters.report_id
            AND family_connections.status = 'connected'
        )
    );

-- Report explanations policies (same as parameters)
CREATE POLICY "Users can view explanations of their reports"
    ON report_explanations FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM report_parameters
            JOIN reports ON reports.id = report_parameters.report_id
            WHERE report_parameters.id = report_explanations.parameter_id
            AND reports.user_id = auth.uid()
        )
    );

-- Family connections policies
CREATE POLICY "Users can view their own connections"
    ON family_connections FOR SELECT
    USING (
        auth.uid() = user_id
        OR auth.uid() = connected_user_id
    );

CREATE POLICY "Users can create connections"
    ON family_connections FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own connections"
    ON family_connections FOR UPDATE
    USING (
        auth.uid() = user_id
        OR auth.uid() = connected_user_id
    );

CREATE POLICY "Users can delete their own connections"
    ON family_connections FOR DELETE
    USING (
        auth.uid() = user_id
        OR auth.uid() = connected_user_id
    );

-- Chat messages policies
CREATE POLICY "Users can view their own chat messages"
    ON chat_messages FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can create their own chat messages"
    ON chat_messages FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Subscriptions policies
CREATE POLICY "Users can view their own subscription"
    ON subscriptions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can update their own subscription"
    ON subscriptions FOR UPDATE
    USING (auth.uid() = user_id);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_reports_updated_at BEFORE UPDATE ON reports
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_family_connections_updated_at BEFORE UPDATE ON family_connections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_subscriptions_updated_at BEFORE UPDATE ON subscriptions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
