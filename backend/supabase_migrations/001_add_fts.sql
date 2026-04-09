-- Migration: Add full-text search (BM25) table for hybrid retrieval
-- This creates a parallel table to vecs.wind_turbine_docs that stores
-- chunk text with a tsvector column for keyword-based search.
--
-- The vecs library manages the vector table (id TEXT, vec VECTOR, metadata JSONB).
-- Text content lives in metadata->>'text'. We mirror the text here with a GIN index
-- so BM25 queries can run alongside dense vector search.
--
-- Usage: Run this SQL in Supabase Dashboard > SQL Editor
-- After running, use reindex_with_context.py to populate the table.

-- ============================================================
-- 1. Full-text search table (parallel to vecs.wind_turbine_docs)
-- ============================================================

CREATE TABLE IF NOT EXISTS public.chunk_fts (
    chunk_id TEXT PRIMARY KEY,         -- matches vecs.wind_turbine_docs.id
    content  TEXT NOT NULL,            -- full chunk text (same as metadata->>'text')
    filename TEXT,                     -- source document filename
    page     INTEGER,                  -- page number (NULL for non-paginated docs)
    language TEXT DEFAULT 'vi',        -- 'en' or 'vi'
    tsv      tsvector GENERATED ALWAYS AS (
        -- Use 'simple' config: no stemming, no stop words.
        -- This works for bilingual VN+EN content where language-specific
        -- configs would miss cross-lingual terms.
        to_tsvector('simple', content)
    ) STORED
);

-- GIN index for fast full-text search
CREATE INDEX IF NOT EXISTS idx_chunk_fts_tsv
    ON public.chunk_fts USING GIN (tsv);

-- Index for filtering by filename (useful for diagnostics)
CREATE INDEX IF NOT EXISTS idx_chunk_fts_filename
    ON public.chunk_fts (filename);


-- ============================================================
-- 2. RPC function: BM25-style keyword search
-- ============================================================
-- Called from Python via: supabase.rpc('search_chunks_fts', {...})
-- Uses websearch_to_tsquery which handles natural language input:
--   "hệ thống phanh" → 'hệ' & 'thống' & 'phanh'
--   "brake OR phanh" → 'brake' | 'phanh'

CREATE OR REPLACE FUNCTION public.search_chunks_fts(
    query_text  TEXT,
    match_count INTEGER DEFAULT 20
)
RETURNS TABLE (
    chunk_id TEXT,
    content  TEXT,
    filename TEXT,
    page     INTEGER,
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
        ts_rank(cf.tsv, websearch_to_tsquery('simple', query_text)) AS rank
    FROM public.chunk_fts cf
    WHERE cf.tsv @@ websearch_to_tsquery('simple', query_text)
    ORDER BY rank DESC
    LIMIT match_count;
$$;


-- ============================================================
-- 3. Helper: Populate chunk_fts from existing vecs data
-- ============================================================
-- One-time backfill if vecs table already has data.
-- After this, new ingestions will write to both tables via Python code.

CREATE OR REPLACE FUNCTION public.backfill_chunk_fts()
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
DECLARE
    inserted_count INTEGER;
BEGIN
    INSERT INTO public.chunk_fts (chunk_id, content, filename, page, language)
    SELECT
        v.id,
        v.metadata->>'text',
        v.metadata->>'filename',
        (v.metadata->>'page')::INTEGER,
        COALESCE(v.metadata->>'language', 'vi')
    FROM vecs.wind_turbine_docs v
    WHERE v.metadata->>'text' IS NOT NULL
    ON CONFLICT (chunk_id) DO UPDATE SET
        content  = EXCLUDED.content,
        filename = EXCLUDED.filename,
        page     = EXCLUDED.page,
        language = EXCLUDED.language;

    GET DIAGNOSTICS inserted_count = ROW_COUNT;
    RETURN inserted_count;
END;
$$;

-- To run the backfill immediately (uncomment if desired):
-- SELECT public.backfill_chunk_fts();
