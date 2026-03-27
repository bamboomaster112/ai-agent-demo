-- =============================================
-- 005: AI Config (Admin-Controllable Parameters)
-- =============================================

CREATE TABLE public.ai_config (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             TEXT UNIQUE NOT NULL,
    value           JSONB NOT NULL,
    description     TEXT,
    min_value       REAL,
    max_value       REAL,
    updated_by      UUID REFERENCES public.user_profiles(id),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Seed defaults
INSERT INTO public.ai_config (key, value, description, min_value, max_value) VALUES
    ('temperature', '{"value": 0.3}', 'Controls randomness. Lower = more deterministic.', 0.0, 1.0),
    ('max_tokens', '{"value": 4096}', 'Maximum output tokens per response.', 256, 16384),
    ('model', '{"value": "claude-sonnet-4-20250514"}', 'Claude model for migration tasks.', NULL, NULL),
    ('classification_model', '{"value": "claude-haiku-4-5-20251001"}', 'Model for detection/classification (cheaper).', NULL, NULL);

-- RLS
ALTER TABLE public.ai_config ENABLE ROW LEVEL SECURITY;

CREATE POLICY "admins_read_ai_config" ON public.ai_config
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );

CREATE POLICY "admins_update_ai_config" ON public.ai_config
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM public.user_profiles WHERE id = auth.uid() AND role = 'admin')
    );
