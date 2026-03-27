-- =============================================
-- 002: Auto-Detection Columns
-- =============================================

ALTER TABLE public.migration_sessions
    ADD COLUMN source_platform TEXT CHECK (source_platform IN ('teamcity', 'jenkins')),
    ADD COLUMN source_format TEXT CHECK (source_format IN ('kotlin_dsl', 'xml', 'json_api', 'groovy')),
    ADD COLUMN config_type TEXT CHECK (config_type IN ('shared_library', 'complete_pipeline', 'fragment')),
    ADD COLUMN detection_method TEXT CHECK (detection_method IN ('heuristic', 'ai', 'user_override')),
    ADD COLUMN detection_confidence REAL DEFAULT 0.0,
    ADD COLUMN user_confirmed BOOLEAN DEFAULT false;
