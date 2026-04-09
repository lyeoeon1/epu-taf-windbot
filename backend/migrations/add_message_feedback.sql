-- Migration: Add message_feedback table for user feedback on chat responses
-- Run this in Supabase Dashboard > SQL Editor

CREATE TABLE IF NOT EXISTS message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_content TEXT NOT NULL,
    feedback_tags TEXT[] NOT NULL DEFAULT '{}',
    feedback_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_message_feedback_session ON message_feedback(session_id);
CREATE INDEX IF NOT EXISTS idx_message_feedback_created ON message_feedback(created_at);

-- Enable RLS (optional, depends on your setup)
-- ALTER TABLE message_feedback ENABLE ROW LEVEL SECURITY;
