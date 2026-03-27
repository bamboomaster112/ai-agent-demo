-- =============================================
-- 001: Core Schema - Users, Sessions, Messages
-- =============================================

-- User profiles (extends Supabase auth.users)
CREATE TABLE public.user_profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL,
    display_name TEXT,
    role        TEXT NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active   BOOLEAN NOT NULL DEFAULT true,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- AI settings (singleton, admin-configurable)
CREATE TABLE public.ai_settings (
    id              INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    model           TEXT NOT NULL DEFAULT 'claude-sonnet-4-20250514',
    temperature     REAL NOT NULL DEFAULT 0.3,
    max_tokens      INT NOT NULL DEFAULT 4096,
    api_key_set     BOOLEAN NOT NULL DEFAULT false,
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Migration sessions
CREATE TABLE public.migration_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    title           TEXT,
    source_type     TEXT NOT NULL CHECK (source_type IN (
        'teamcity_kotlin', 'teamcity_xml', 'teamcity_json', 'jenkins'
    )),
    source_content  TEXT,
    status          TEXT NOT NULL DEFAULT 'in_progress' CHECK (status IN (
        'in_progress', 'completed', 'failed'
    )),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Chat messages
CREATE TABLE public.messages (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES public.migration_sessions(id) ON DELETE CASCADE,
    role            TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content         TEXT NOT NULL,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Generated workflow files
CREATE TABLE public.generated_workflows (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES public.migration_sessions(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL DEFAULT '.github/workflows/ci.yml',
    yaml_content    TEXT NOT NULL,
    notes           JSONB DEFAULT '[]',
    version         INT NOT NULL DEFAULT 1,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Uploaded files (metadata; blobs in Supabase Storage)
CREATE TABLE public.uploads (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL REFERENCES public.migration_sessions(id) ON DELETE CASCADE,
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    storage_path    TEXT NOT NULL,
    file_name       TEXT NOT NULL,
    mime_type       TEXT NOT NULL,
    file_size       INT NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Usage / analytics
CREATE TABLE public.usage_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    session_id      UUID REFERENCES public.migration_sessions(id) ON DELETE SET NULL,
    action          TEXT NOT NULL,
    tokens_in       INT DEFAULT 0,
    tokens_out      INT DEFAULT 0,
    model_used      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Indexes
CREATE INDEX idx_sessions_user ON public.migration_sessions(user_id);
CREATE INDEX idx_messages_session ON public.messages(session_id);
CREATE INDEX idx_workflows_session ON public.generated_workflows(session_id);
CREATE INDEX idx_uploads_session ON public.uploads(session_id);
CREATE INDEX idx_usage_user ON public.usage_logs(user_id);

-- Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.migration_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.generated_workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.uploads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies: users see own data
CREATE POLICY "users_own_profile" ON public.user_profiles
    FOR ALL USING (auth.uid() = id);

CREATE POLICY "admins_read_all_profiles" ON public.user_profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "users_own_sessions" ON public.migration_sessions
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users_own_messages" ON public.messages
    FOR ALL USING (
        session_id IN (SELECT id FROM public.migration_sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "users_own_workflows" ON public.generated_workflows
    FOR ALL USING (
        session_id IN (SELECT id FROM public.migration_sessions WHERE user_id = auth.uid())
    );

CREATE POLICY "users_own_uploads" ON public.uploads
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users_own_usage" ON public.usage_logs
    FOR SELECT USING (user_id = auth.uid());

CREATE POLICY "admins_read_all_usage" ON public.usage_logs
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

-- Seed AI settings
INSERT INTO public.ai_settings (id) VALUES (1);

-- Auto-create user_profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
