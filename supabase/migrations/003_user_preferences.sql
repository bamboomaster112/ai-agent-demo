-- =============================================
-- 003: User Preferences / Memory System
-- =============================================

CREATE TABLE public.user_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    category        TEXT NOT NULL,
    preference_key  TEXT NOT NULL,
    preference_value TEXT NOT NULL,
    source          TEXT NOT NULL CHECK (source IN ('explicit', 'inferred', 'manual')),
    source_message_id UUID,
    confidence      REAL DEFAULT 1.0,
    active          BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(user_id, category, preference_key)
);

CREATE INDEX idx_user_prefs_user ON public.user_preferences(user_id) WHERE active = true;

CREATE TABLE public.preference_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    preference_id   UUID REFERENCES public.user_preferences(id),
    action          TEXT NOT NULL,
    old_value       TEXT,
    new_value       TEXT,
    migration_id    UUID,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- RLS
ALTER TABLE public.user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.preference_audit_log ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_own_preferences" ON public.user_preferences
    FOR ALL USING (user_id = auth.uid());

CREATE POLICY "users_own_pref_audit" ON public.preference_audit_log
    FOR SELECT USING (
        preference_id IN (SELECT id FROM public.user_preferences WHERE user_id = auth.uid())
    );
