# Local Development Setup

Complete guide to running the AI CI/CD Migration Agent locally for development.

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.11+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| Git | any | `git --version` |

**API keys required:**

| Service | Where to get it |
|---------|----------------|
| Supabase | [supabase.com/dashboard](https://supabase.com/dashboard) → Project Settings → API |
| Anthropic (Claude) | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| Voyage AI (embeddings) | [dash.voyageai.com](https://dash.voyageai.com) → API Keys |

## 1. Clone the Repository

```bash
git clone https://github.com/bamboomaster112/ai-agent-demo.git
cd ai-agent-demo
```

## 2. Set Up Supabase

Follow the [Supabase Setup Guide](supabase-setup.md) to:

1. Create a Supabase project (cloud)
2. Run the 5 SQL migrations
3. Create the `migration-uploads` Storage bucket

Come back here once Supabase is configured.

## 3. Configure Environment Variables

### Backend

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your-key
SUPABASE_SECRET_KEY=sb_secret_your-key
ANTHROPIC_API_KEY=sk-ant-your-key
VOYAGE_API_KEY=pa-your-key
SECRET_KEY=generate-a-random-string-here
```

> See [Environment Variables Reference](environment-variables.md) for all options.

### Frontend

```bash
cp frontend/.env.example frontend/.env
```

Edit `frontend/.env`:

```env
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_your-key
VITE_API_URL=http://localhost:8000
```

## 4. Start the Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/api/health
# Expected: {"status": "ok"}
```

## 5. Start the Frontend

Open a new terminal:

```bash
cd frontend
npm install
npm run dev
```

The app will be available at **http://localhost:5173**.

## 6. First-Time Setup

### Create your account

1. Open http://localhost:5173
2. Click **Sign Up**
3. Enter your email and password

### Promote yourself to admin

The first user needs to be manually promoted. Run this in the Supabase SQL Editor (or via `psql`):

```sql
UPDATE public.user_profiles
SET role = 'admin'
WHERE email = 'your-email@example.com';
```

### Verify admin access

Log in again. You should now see the **Admin** section in the navigation with access to:
- User Management
- AI Settings (model, temperature, max tokens)
- RAG Settings (chunk size, top-k, similarity threshold)
- Analytics

## 7. Running Tests

```bash
cd backend
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run a specific test file:

```bash
pytest tests/test_detection.py -v
```

## Troubleshooting

### `ModuleNotFoundError: No module named 'app'`

Make sure you installed the backend in editable mode:

```bash
cd backend
pip install -e ".[dev]"
```

### `CORS errors in browser console`

Check that `FRONTEND_URL` in `.env` matches the URL where the frontend is running (default: `http://localhost:5173`).

### `401 Unauthorized on API calls`

- Verify `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` match between backend `.env` and frontend `.env`
- Check that your Supabase project is active
- Try logging out and back in

### `Connection refused on port 8000`

Make sure the backend is running: `uvicorn app.main:app --reload --port 8000`

### `pgvector extension not found`

If using Supabase Cloud, pgvector is available by default. Make sure migration `004_rag_tables.sql` has been run (it includes `CREATE EXTENSION IF NOT EXISTS vector;`).

---

**Next:** [Docker Setup](setup-docker.md) | [Supabase Setup](supabase-setup.md) | [Architecture](architecture.md)
