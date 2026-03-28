# Supabase Setup

This guide walks through setting up Supabase for the AI CI/CD Migration Agent, including the database schema, storage bucket, and authentication.

## Option A: Supabase Cloud (Recommended)

### 1. Create a Project

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Click **New Project**
3. Choose an organization, enter a project name, and set a database password
4. Select a region close to your users
5. Click **Create new project** and wait for provisioning (~2 minutes)

### 2. Get Your API Keys

Go to **Project Settings** → **API** and copy:

| Key | Environment Variable | Description |
|-----|---------------------|-------------|
| Project URL | `SUPABASE_URL` | `https://your-project.supabase.co` |
| Publishable key (anon) | `SUPABASE_PUBLISHABLE_KEY` | Safe for frontend, respects RLS |
| Secret key (service_role) | `SUPABASE_SECRET_KEY` | Backend only, bypasses RLS |

> **Note:** Supabase recently renamed these keys. The "anon" key is now called "publishable" (prefixed `sb_publishable_`), and the "service_role" key is now called "secret" (prefixed `sb_secret_`). Older projects may still show the old names — the keys themselves are the same.

### 3. Run Database Migrations

Go to **SQL Editor** in your Supabase dashboard and run each migration file **in order**. Copy and paste the full contents of each file:

| Order | File | What it creates |
|-------|------|----------------|
| 1 | `supabase/migrations/001_initial_schema.sql` | Core tables: `user_profiles`, `ai_settings`, `migration_sessions`, `messages`, `generated_workflows`, `uploads`, `usage_logs`. RLS policies. Auto-profile trigger. |
| 2 | `supabase/migrations/002_detection_columns.sql` | Adds auto-detection columns to `migration_sessions`: `source_platform`, `source_format`, `config_type`, `detection_method`, `detection_confidence`, `user_confirmed` |
| 3 | `supabase/migrations/003_user_preferences.sql` | Memory system: `user_preferences` (with upsert on user+category+key), `preference_audit_log`. RLS policies. |
| 4 | `supabase/migrations/004_rag_tables.sql` | Enables pgvector extension. Creates `documents`, `document_chunks` (with `vector(1024)` embeddings), `rag_config`. IVFFlat index. `match_document_chunks()` similarity search function. |
| 5 | `supabase/migrations/005_ai_config.sql` | Admin-configurable AI parameters: `ai_config` table with seeded defaults (temperature, max_tokens, model, classification_model). |

**Run them in order** — later migrations depend on tables created by earlier ones.

#### Quick method (copy all at once)

You can also concatenate all migrations and run them as a single SQL script. In a terminal:

```bash
cat supabase/migrations/001_initial_schema.sql \
    supabase/migrations/002_detection_columns.sql \
    supabase/migrations/003_user_preferences.sql \
    supabase/migrations/004_rag_tables.sql \
    supabase/migrations/005_ai_config.sql
```

Copy the output and paste it into the Supabase SQL Editor, then click **Run**.

### 4. Create the Storage Bucket

The app uses Supabase Storage for file uploads (screenshots, pipeline configs).

1. Go to **Storage** in the Supabase dashboard
2. Click **New bucket**
3. Name: `migration-uploads`
4. Set to **Private** (files accessed via signed URLs)
5. Click **Create bucket**

Allowed file types are enforced by the backend, not at the bucket level:
- Images: PNG, JPEG, GIF, WebP
- Text: plain text, XML
- Data: JSON, XML

### 5. Verify Setup

After running migrations, verify in the **Table Editor**:

- `user_profiles` table exists (empty until first signup)
- `ai_config` table has 4 rows (temperature, max_tokens, model, classification_model)
- `rag_config` table has 5 rows (chunk_size, chunk_overlap, top_k, similarity_threshold, embedding_model)
- `ai_settings` table has 1 row (seeded defaults)

Check that pgvector is enabled:

```sql
SELECT * FROM pg_extension WHERE extname = 'vector';
```

## Option B: Local Docker PostgreSQL

The `docker-compose.yml` includes a local PostgreSQL service with pgvector support.

```yaml
supabase-db:
  image: supabase/postgres:15.6.1.143
  ports:
    - "5432:5432"
  environment:
    POSTGRES_PASSWORD: postgres
    POSTGRES_DB: postgres
  volumes:
    - supabase-data:/var/lib/postgresql/data
    - ./supabase/migrations:/docker-entrypoint-initdb.d
```

**What works locally:**
- All tables, indexes, functions, and RLS policies
- pgvector extension and similarity search
- Direct SQL queries

**What doesn't work locally:**
- Supabase Auth (`auth.users`, `auth.uid()`, JWT validation) — the `handle_new_user` trigger references `auth.users` which only exists in Supabase
- Supabase Storage (file uploads/downloads)
- Supabase Realtime

**Recommendation:** Use Supabase Cloud for development. The local DB is useful for testing migrations and schema changes, but the app needs Supabase Auth and Storage for full functionality.

### Connecting to the local DB

```bash
# Via Docker
docker-compose exec supabase-db psql -U postgres

# Via psql directly
psql -h localhost -p 5432 -U postgres -d postgres
# Password: postgres
```

## Database Schema Overview

### Entity Relationship Diagram

```
auth.users (Supabase Auth)
    │
    ├──→ user_profiles (1:1, auto-created by trigger)
    │        │
    │        ├──→ migration_sessions (1:N)
    │        │        │
    │        │        ├──→ messages (1:N)
    │        │        ├──→ generated_workflows (1:N)
    │        │        └──→ uploads (1:N)
    │        │
    │        ├──→ user_preferences (1:N)
    │        │        └──→ preference_audit_log (1:N)
    │        │
    │        ├──→ usage_logs (1:N)
    │        │
    │        └──→ documents (1:N, nullable)
    │                 └──→ document_chunks (1:N, with vector embeddings)
    │
    ├── ai_settings (singleton)
    ├── ai_config (admin-only key-value)
    └── rag_config (admin-only key-value)
```

### Tables

| Table | Purpose | RLS |
|-------|---------|-----|
| `user_profiles` | User accounts with role (user/admin) | Users see own; admins see all |
| `migration_sessions` | Pipeline migration sessions | Users see own only |
| `messages` | Chat conversation history | Via session ownership |
| `generated_workflows` | Generated GitHub Actions YAML | Via session ownership |
| `uploads` | File upload metadata | Users see own only |
| `usage_logs` | Token usage tracking | Users see own; admins see all |
| `user_preferences` | Learned user preferences | Users see own only |
| `preference_audit_log` | Preference change history | Via preference ownership |
| `documents` | RAG documents | Users see own + system docs; admins all |
| `document_chunks` | Vectorized chunks with embeddings | Via document ownership |
| `ai_settings` | Legacy singleton AI config | — |
| `ai_config` | Admin-tunable AI parameters | Admins only |
| `rag_config` | Admin-tunable RAG parameters | Admins only |

### Key Functions

#### `handle_new_user()` (trigger)

Automatically creates a `user_profiles` row when a new user signs up via Supabase Auth:

```sql
-- Triggered by: AFTER INSERT ON auth.users
INSERT INTO public.user_profiles (id, email, display_name)
VALUES (NEW.id, NEW.email, COALESCE(NEW.raw_user_meta_data->>'display_name', split_part(NEW.email, '@', 1)));
```

#### `match_document_chunks()` (RPC function)

Semantic similarity search used by the RAG system:

```sql
match_document_chunks(
    query_embedding vector(1024),  -- Voyage AI embedding
    match_threshold FLOAT DEFAULT 0.75,
    match_count INT DEFAULT 5,
    filter_doc_type TEXT DEFAULT NULL,
    filter_platform TEXT DEFAULT NULL
)
-- Returns: id, document_id, chunk_index, content, metadata, similarity
```

## Common Admin Tasks

### Promote a user to admin

```sql
UPDATE public.user_profiles
SET role = 'admin'
WHERE email = 'user@example.com';
```

### Reset a user's role to regular user

```sql
UPDATE public.user_profiles
SET role = 'user'
WHERE email = 'user@example.com';
```

### Deactivate a user account

```sql
UPDATE public.user_profiles
SET is_active = false
WHERE email = 'user@example.com';
```

### Check RAG configuration

```sql
SELECT key, value FROM public.rag_config ORDER BY key;
```

### Check AI model configuration

```sql
SELECT key, value, description FROM public.ai_config ORDER BY key;
```

### View usage statistics

```sql
SELECT
    u.email,
    COUNT(*) as total_requests,
    SUM(ul.tokens_in) as total_input_tokens,
    SUM(ul.tokens_out) as total_output_tokens
FROM public.usage_logs ul
JOIN public.user_profiles u ON ul.user_id = u.id
GROUP BY u.email
ORDER BY total_requests DESC;
```

---

**Next:** [Local Setup](setup-local.md) | [Docker Setup](setup-docker.md) | [Environment Variables](environment-variables.md)
