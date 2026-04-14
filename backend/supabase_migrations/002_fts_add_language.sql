-- Migration: Add language column to search_chunks_fts RPC result
-- Required for Vietnamese document priority feature.
--
-- Usage: Run this SQL in Supabase Dashboard > SQL Editor

CREATE OR REPLACE FUNCTION public.search_chunks_fts(
    query_text  TEXT,
    match_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    chunk_id TEXT,
    content  TEXT,
    filename TEXT,
    page     INTEGER,
    language TEXT,
    rank     REAL
)
LANGUAGE sql
STABLE
AS $$
    SELECT
        cf.chunk_id,
        cf.content,
        cf.filename,
        cf.page,
        cf.language,
        ts_rank(cf.tsv, websearch_to_tsquery('simple', query_text)) AS rank
    FROM public.chunk_fts cf
    WHERE cf.tsv @@ websearch_to_tsquery('simple', query_text)
    ORDER BY rank DESC
    LIMIT match_count;
$$;
