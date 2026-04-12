-- Migration: Add global_corrections table for cross-session correction persistence
-- Run this in Supabase Dashboard > SQL Editor

-- Global corrections: persist validated corrections across all sessions.
-- When a user corrects the bot and gives positive feedback, the correction
-- is promoted here so all future sessions benefit from it.
CREATE TABLE IF NOT EXISTS global_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity TEXT NOT NULL,
    attribute TEXT NOT NULL,
    old_value TEXT DEFAULT '',
    new_value TEXT NOT NULL,
    source_session_id UUID REFERENCES chat_sessions(id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    UNIQUE(entity, attribute)
);

CREATE INDEX IF NOT EXISTS idx_global_corrections_active
    ON global_corrections(is_active) WHERE is_active = TRUE;

-- Reuse existing update_updated_at_column() function from chat_sessions
CREATE TRIGGER update_global_corrections_updated_at
    BEFORE UPDATE ON global_corrections
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
