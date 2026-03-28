# Environment Variables Reference

Complete reference for all configuration variables used by the AI CI/CD Migration Agent.

## Backend (`.env`)

The backend loads environment variables from `.env` in the project root.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUPABASE_URL` | Yes | — | Supabase project URL (e.g., `https://abc123.supabase.co`) |
| `SUPABASE_PUBLISHABLE_KEY` | Yes | — | Supabase publishable key (formerly "anon key"). Prefixed `sb_publishable_`. Used for frontend client. |
| `SUPABASE_SECRET_KEY` | Yes | — | Supabase secret key (formerly "service_role key"). Prefixed `sb_secret_`. Used by backend to bypass RLS. |
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key for Claude. Prefixed `sk-ant-`. |
| `VOYAGE_API_KEY` | Yes | — | Voyage AI API key for embeddings. Prefixed `pa-`. |
| `BACKEND_URL` | No | `http://localhost:8000` | Backend URL (used internally). |
| `FRONTEND_URL` | No | `http://localhost:5173` | Frontend URL. Used for CORS origin configuration. |
| `SECRET_KEY` | Yes | `change-this-to-a-random-secret` | Secret key for signing. **Change this in production.** |
| `DEFAULT_MODEL` | No | `claude-sonnet-4-20250514` | Default Claude model for migration tasks. Overridable by admin in the UI. |
| `DEFAULT_TEMPERATURE` | No | `0.3` | Default temperature (0.0-1.0). Lower = more deterministic. Overridable by admin. |
| `DEFAULT_MAX_TOKENS` | No | `4096` | Default max output tokens (256-16384). Overridable by admin. |

### Example `.env`

```env
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxxxxxxxxxxxxxxxx
SUPABASE_SECRET_KEY=sb_secret_xxxxxxxxxxxxxxxxxxxx

# AI Services
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxx
VOYAGE_API_KEY=pa-xxxxxxxxxxxxxxxxxxxx

# App Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
SECRET_KEY=your-random-secret-string-here

# AI Defaults (overridable by admin via UI)
DEFAULT_MODEL=claude-sonnet-4-20250514
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=4096
```

## Frontend (`frontend/.env`)

The frontend loads environment variables from `frontend/.env`. Variables must be prefixed with `VITE_` to be accessible in client-side code.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VITE_SUPABASE_URL` | Yes | — | Supabase project URL. Must match backend's `SUPABASE_URL`. |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Yes | — | Supabase publishable key. Must match backend's `SUPABASE_PUBLISHABLE_KEY`. |
| `VITE_API_URL` | Yes | `http://localhost:8000` | Backend API URL. Frontend sends API requests here. |

### Example `frontend/.env`

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_xxxxxxxxxxxxxxxxxxxx
VITE_API_URL=http://localhost:8000
```

## Where to Get API Keys

### Supabase

1. Go to [supabase.com/dashboard](https://supabase.com/dashboard)
2. Select your project (or create one)
3. Navigate to **Settings** → **API**
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **Project API keys** → anon/publishable → `SUPABASE_PUBLISHABLE_KEY`
   - **Project API keys** → service_role/secret → `SUPABASE_SECRET_KEY`

> The publishable key is safe to expose in frontend code. The secret key must **never** be exposed to the client.

### Anthropic (Claude)

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Navigate to **API Keys**
3. Click **Create Key**
4. Copy the key → `ANTHROPIC_API_KEY`

**Pricing:** Claude API usage is billed per token. The app uses:
- **Claude Sonnet** for migration tasks (configurable by admin)
- **Claude Haiku** for detection/classification (cheaper, configurable by admin)

### Voyage AI (Embeddings)

1. Go to [dash.voyageai.com](https://dash.voyageai.com)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create and copy the key → `VOYAGE_API_KEY`

**Model used:** `voyage-3.5` (1024 dimensions). Configurable via admin RAG settings.

**Pricing:** Voyage AI charges per token embedded. Embedding happens during:
- RAG document ingestion (one-time per document)
- Query embedding during migration chat (per message)

## Docker-Specific Notes

When running with Docker Compose, the environment variables are loaded from the same `.env` files:

- Backend service: loads from `.env` (project root)
- Frontend service: loads from `frontend/.env`

The local `supabase-db` Docker service uses hardcoded credentials:
- Host: `localhost` (or `supabase-db` from within Docker network)
- Port: `5432`
- User: `postgres`
- Password: `postgres`
- Database: `postgres`

> **Note:** The backend still connects to **Supabase Cloud** (via `SUPABASE_URL`), not the local Docker PostgreSQL. The local DB is for migration testing only.

## Security Notes

- Never commit `.env` files to version control (they're in `.gitignore`)
- The `SECRET_KEY` should be a long random string in production. Generate one with:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- `SUPABASE_SECRET_KEY` bypasses all Row Level Security — keep it server-side only
- `VITE_SUPABASE_PUBLISHABLE_KEY` is safe for client-side code (RLS protects data)
- Rotate API keys if they are ever exposed

---

**Next:** [Local Setup](setup-local.md) | [Docker Setup](setup-docker.md) | [Architecture](architecture.md)
