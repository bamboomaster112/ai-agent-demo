-- =============================================
-- 004: RAG System (pgvector + Documents + Chunks)
-- =============================================

CREATE EXTENSION IF NOT EXISTS vector;

-- Documents (reference docs, past migrations, pipeline configs)
CREATE TABLE public.documents (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    doc_type        TEXT NOT NULL CHECK (doc_type IN (
        'pipeline_config', 'migration_result', 'reference_doc', 'actions_doc'
    )),
    source_platform TEXT,
    title           TEXT,
    original_content TEXT,
    metadata        JSONB DEFAULT '{}',
    user_id         UUID REFERENCES public.user_profiles(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Document chunks with embeddings
CREATE TABLE public.document_chunks (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES public.documents(id) ON DELETE CASCADE,
    chunk_index     INTEGER NOT NULL,
    content         TEXT NOT NULL,
    token_count     INTEGER,
    embedding       vector(1024),
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_chunks_document ON public.document_chunks(document_id);
CREATE INDEX idx_documents_type ON public.documents(doc_type, source_platform);

-- IVFFlat index for vector similarity search
CREATE INDEX idx_chunks_embedding ON public.document_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- RAG configuration (admin-controllable)
CREATE TABLE public.rag_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             TEXT UNIQUE NOT NULL,
    value           JSONB NOT NULL,
    updated_by      UUID REFERENCES public.user_profiles(id),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed default RAG config
INSERT INTO public.rag_config (key, value) VALUES
    ('chunk_size', '{"tokens": 512}'),
    ('chunk_overlap', '{"tokens": 64}'),
    ('top_k', '{"value": 5}'),
    ('similarity_threshold', '{"value": 0.75}'),
    ('embedding_model', '{"value": "voyage-3.5"}');

-- RLS
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.document_chunks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.rag_config ENABLE ROW LEVEL SECURITY;

-- Users can see their own documents + system documents (user_id IS NULL)
CREATE POLICY "users_own_or_system_docs" ON public.documents
    FOR SELECT USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "users_insert_own_docs" ON public.documents
    FOR INSERT WITH CHECK (user_id = auth.uid());

CREATE POLICY "admins_all_docs" ON public.documents
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "chunks_via_documents" ON public.document_chunks
    FOR SELECT USING (
        document_id IN (
            SELECT id FROM public.documents
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );

CREATE POLICY "admins_read_rag_config" ON public.rag_config
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "admins_update_rag_config" ON public.rag_config
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Similarity search function
CREATE OR REPLACE FUNCTION match_document_chunks(
    query_embedding vector(1024),
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    filter_doc_type TEXT DEFAULT NULL,
    filter_platform TEXT DEFAULT NULL
)
RETURNS TABLE (
    id UUID,
    document_id UUID,
    chunk_index INTEGER,
    content TEXT,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.chunk_index,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM public.document_chunks dc
    JOIN public.documents d ON dc.document_id = d.id
    WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
        AND (filter_doc_type IS NULL OR d.doc_type = filter_doc_type)
        AND (filter_platform IS NULL OR d.source_platform = filter_platform)
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
