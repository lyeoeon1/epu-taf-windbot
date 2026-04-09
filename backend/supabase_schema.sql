-- Enable pgvector extension (run this first in Supabase Dashboard > Database > Extensions)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- Chat sessions
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT DEFAULT 'New Chat',
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'vi')),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE 'plpgsql';

CREATE TRIGGER update_chat_sessions_updated_at
    BEFORE UPDATE ON chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Chat messages
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_chat_messages_session ON chat_messages(session_id, created_at);

-- Documents metadata (tracking ingested files)
CREATE TABLE documents_metadata (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename TEXT NOT NULL,
    file_type TEXT,
    language TEXT DEFAULT 'en' CHECK (language IN ('en', 'vi')),
    title TEXT,
    num_chunks INTEGER DEFAULT 0,
    ingested_at TIMESTAMPTZ DEFAULT now()
);

-- Glossary (bilingual wind turbine terminology)
CREATE TABLE glossary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    term_en TEXT NOT NULL UNIQUE,
    term_vi TEXT NOT NULL,
    definition_en TEXT NOT NULL,
    definition_vi TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'structure', 'components', 'operations',
        'maintenance', 'safety', 'troubleshooting', 'general'
    )),
    abbreviation TEXT,
    related_terms TEXT[],
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_glossary_term_en ON glossary USING GIN (to_tsvector('english', term_en));
CREATE INDEX idx_glossary_category ON glossary(category);

CREATE TRIGGER update_glossary_updated_at
    BEFORE UPDATE ON glossary
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- User feedback on chat messages
CREATE TABLE IF NOT EXISTS message_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    message_content TEXT NOT NULL,
    feedback_tags TEXT[] NOT NULL DEFAULT '{}',
    feedback_text TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_message_feedback_session ON message_feedback(session_id);
CREATE INDEX idx_message_feedback_created ON message_feedback(created_at);
