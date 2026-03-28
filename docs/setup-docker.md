# Docker Setup

Run the entire AI CI/CD Migration Agent stack using Docker Compose.

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Docker | 20+ | `docker --version` |
| Docker Compose | v2+ | `docker compose version` |

**API keys required** (same as local setup):

| Service | Where to get it |
|---------|----------------|
| Anthropic (Claude) | [console.anthropic.com](https://console.anthropic.com) → API Keys |
| Voyage AI (embeddings) | [dash.voyageai.com](https://dash.voyageai.com) → API Keys |
| Supabase (cloud) | [supabase.com/dashboard](https://supabase.com/dashboard) → Project Settings → API |

## Architecture

Docker Compose runs 3 services:

```
┌─────────────────────────────┐
│  frontend  (port 5173)      │  React + Vite dev server
├─────────────────────────────┤
│  backend   (port 8000)      │  FastAPI + Uvicorn
├─────────────────────────────┤
│  supabase-db (port 5432)    │  PostgreSQL 15.6 + pgvector
└─────────────────────────────┘
```

> **Important:** The Docker `supabase-db` service provides a local PostgreSQL database, but it does **not** include Supabase Auth or Supabase Storage. For full functionality (authentication, file uploads), you need a **Supabase Cloud project**. The local DB is useful for schema/data work, but the app should connect to Supabase Cloud for production use.

## 1. Set Up Supabase Cloud

Follow the [Supabase Setup Guide](supabase-setup.md) to create your project, run migrations, and create the storage bucket.

## 2. Configure Environment Variables

### Backend

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Point to your Supabase Cloud project (NOT the local Docker DB)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_PUBLISHABLE_KEY=sb_publishable_your-key
SUPABASE_SECRET_KEY=sb_secret_your-key

# AI keys
ANTHROPIC_API_KEY=sk-ant-your-key
VOYAGE_API_KEY=pa-your-key

# Backend config
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:5173
SECRET_KEY=generate-a-random-string-here

# Defaults (overridable by admin in the UI)
DEFAULT_MODEL=claude-sonnet-4-20250514
DEFAULT_TEMPERATURE=0.3
DEFAULT_MAX_TOKENS=4096
```

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

> See [Environment Variables Reference](environment-variables.md) for details on each variable.

## 3. Build and Start

```bash
docker-compose up --build
```

This will:
1. Build the **backend** image (Python 3.11 + dependencies from `pyproject.toml`)
2. Build the **frontend** image (Node 22 + dependencies from `package.json`)
3. Start **supabase-db** (PostgreSQL 15.6 with pgvector)
4. Auto-run SQL migrations from `supabase/migrations/` into the local DB

Wait until you see output from all three services, then open:
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000/api/health
- **Database:** `localhost:5432` (user: `postgres`, password: `postgres`)

## 4. First-Time Setup

### Create your account

1. Open http://localhost:5173
2. Click **Sign Up** and create an account

### Promote to admin

Connect to your Supabase project's SQL Editor and run:

```sql
UPDATE public.user_profiles
SET role = 'admin'
WHERE email = 'your-email@example.com';
```

## 5. Common Operations

### Stop all services

```bash
docker-compose down
```

### Stop and remove data volumes

```bash
docker-compose down -v
```

> **Warning:** This deletes the local PostgreSQL data. Your Supabase Cloud data is unaffected.

### Rebuild after code changes

```bash
docker-compose up --build
```

> In development mode, both backend and frontend have **hot reload** enabled via volume mounts, so most code changes take effect automatically without rebuilding.

### View logs for a specific service

```bash
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f supabase-db
```

### Access the local database

```bash
docker-compose exec supabase-db psql -U postgres
```

## 6. Using Local Database Only (Advanced)

If you want to use the Docker PostgreSQL instead of Supabase Cloud for database operations (without Auth/Storage):

1. The SQL migrations auto-run on first boot from `./supabase/migrations/`
2. Connect your backend to local DB by adjusting your Supabase client config
3. Note: Supabase Auth (`auth.users`, `auth.uid()`) and Storage won't be available locally

This setup is mainly useful for:
- Testing SQL migrations
- Developing database-heavy features
- Running in environments without internet access (AI features won't work without API keys)

For full functionality, use Supabase Cloud.

## Docker Service Details

### Backend (`backend/Dockerfile`)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- Volume mount: `./backend:/app` (enables hot reload)
- Command override: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`

### Frontend (`frontend/Dockerfile`)

```dockerfile
FROM node:22-slim
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

- Volume mount: `./frontend:/app` + `/app/node_modules` (preserves container's node_modules)
- Dev server bound to `0.0.0.0` for Docker network access

### Supabase DB

- Image: `supabase/postgres:15.6.1.143` (includes pgvector)
- Auto-runs `.sql` files from `./supabase/migrations/` on first boot
- Data persisted in `supabase-data` Docker volume
- Default credentials: `postgres` / `postgres`

## Troubleshooting

### Frontend can't reach backend

Both services run on the Docker host network. Ensure `VITE_API_URL=http://localhost:8000` in `frontend/.env`.

### Database migrations didn't run

Migrations only auto-run on **first** database creation. If the volume already exists:

```bash
docker-compose down -v    # Remove volumes
docker-compose up --build # Recreate from scratch
```

Or manually run migrations:

```bash
docker-compose exec supabase-db psql -U postgres -f /docker-entrypoint-initdb.d/001_initial_schema.sql
# Repeat for 002, 003, 004, 005
```

### Port conflicts

If ports 5173, 8000, or 5432 are already in use, either stop the conflicting process or update `docker-compose.yml` port mappings.

### Container keeps restarting

Check logs for the failing service:

```bash
docker-compose logs backend
```

Common causes:
- Missing or invalid environment variables in `.env`
- Python dependency installation failures (network issues)

---

**Next:** [Local Setup](setup-local.md) | [Supabase Setup](supabase-setup.md) | [Architecture](architecture.md)
