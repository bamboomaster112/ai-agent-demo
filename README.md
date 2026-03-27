# AI CI/CD Migration Agent

An AI-powered application that helps migrate CI/CD pipelines from **TeamCity** and **Jenkins** to **GitHub Actions**.

## Features

- **Auto-Detection**: Automatically identifies pipeline type (TeamCity/Jenkins), format (Kotlin DSL, XML, JSON, Groovy), and config type (shared library, complete pipeline, fragment) using a two-tier system (heuristic regex patterns + Claude AI fallback)
- **AI-Powered Migration**: Chat-based interface with streaming SSE responses powered by Claude (Anthropic)
- **Screenshot Analysis**: Upload screenshots of pipeline UIs for vision-based analysis via Claude's vision API
- **RAG Support**: Context-aware retrieval using pgvector with format-specific chunking (Jenkins stages, TeamCity buildTypes, XML elements, Markdown headings) and Voyage AI embeddings
- **User Preferences/Memory**: Learns and remembers user preferences across sessions via regex extraction and AI-assisted inference
- **Admin Controls**: Model selection, temperature tuning, RAG parameters (chunk size, top-k, similarity threshold), user management, and usage analytics

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React + Vite (TypeScript) + Tailwind CSS
- **AI**: Claude API (Anthropic) for migration and classification
- **Embeddings**: Voyage AI (`voyage-3.5`, 1024 dimensions) - Anthropic's official embedding partner
- **Database**: Supabase (PostgreSQL + pgvector + Auth + Storage)
- **Streaming**: SSE via `sse-starlette`

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (or local Supabase via Docker)
- Anthropic API key
- Voyage AI API key ([voyageai.com](https://www.voyageai.com))

### Backend Setup

```bash
cd backend
pip install -e ".[dev]"
cp ../.env.example ../.env  # Edit with your keys
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env  # Edit with your Supabase URL/key
npm run dev
```

### Docker

```bash
docker-compose up --build
```

## Environment Variables

### Backend (`.env`)

Copy `.env.example` and fill in your values:

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key (formerly anon key, prefixed `sb_publishable_`) |
| `SUPABASE_SECRET_KEY` | Supabase secret key (formerly service role key, prefixed `sb_secret_`) |
| `ANTHROPIC_API_KEY` | Anthropic API key for Claude |
| `VOYAGE_API_KEY` | Voyage AI API key for embeddings |
| `BACKEND_URL` | Backend URL (default: `http://localhost:8000`) |
| `FRONTEND_URL` | Frontend URL for CORS (default: `http://localhost:5173`) |
| `SECRET_KEY` | Secret key for session signing |
| `DEFAULT_MODEL` | Default Claude model (default: `claude-sonnet-4-20250514`) |
| `DEFAULT_TEMPERATURE` | Default temperature (default: `0.3`) |
| `DEFAULT_MAX_TOKENS` | Default max tokens (default: `4096`) |

### Frontend (`frontend/.env`)

| Variable | Description |
|----------|-------------|
| `VITE_SUPABASE_URL` | Your Supabase project URL |
| `VITE_SUPABASE_PUBLISHABLE_KEY` | Supabase publishable key |
| `VITE_API_URL` | Backend API URL (default: `http://localhost:8000`) |

## API Endpoints

### Auth `/api/auth`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/signup` | Register new user |
| POST | `/login` | Login, returns JWT |
| POST | `/refresh` | Refresh token |
| GET | `/me` | Current user + profile |

### Migrations `/api/migrations`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Create session (auto-detects pipeline type) |
| GET | `/` | List user's sessions |
| GET | `/{id}` | Session detail + messages + workflows |
| DELETE | `/{id}` | Delete session |
| POST | `/{id}/messages` | Send message (returns SSE stream) |
| GET | `/{id}/messages` | Message history |

### Detection `/api/detect`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Auto-detect file type + config type |
| PUT | `/migrations/{id}/detection` | User override |
| POST | `/migrations/{id}/confirm-detection` | Confirm and proceed |

### Uploads `/api/uploads`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/` | Upload file (images, configs) |
| GET | `/{id}/url` | Get signed download URL |

### Memory `/api/users/me/preferences`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | List active preferences |
| POST | `/` | Add preference manually |
| PUT | `/{id}` | Update preference |
| DELETE | `/{id}` | Soft-delete preference |
| POST | `/extract/{session_id}` | AI-extract preferences from conversation |

### RAG `/api/rag`
| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents` | Upload reference document |
| GET | `/documents` | List documents |
| DELETE | `/documents/{id}` | Remove document + chunks |
| POST | `/search` | Semantic search |
| GET/PUT | `/config` | RAG configuration |

### Admin `/api/admin`
| Method | Path | Description |
|--------|------|-------------|
| GET | `/users` | List all users |
| PATCH | `/users/{id}` | Update role/active status |
| GET/PUT | `/ai-config` | AI model settings |
| POST | `/preview` | Dry-run migration with custom params |
| GET | `/analytics` | Usage statistics |

### SSE Stream Events

When sending a message via `POST /api/migrations/{id}/messages`, the response is an SSE stream:

```
event: token    → {"text": "..."}           # Streaming text chunks
event: yaml     → {"filename": "...", ...}  # Extracted GitHub Actions workflow
event: note     → {"level": "warning", ...} # Migration notes/warnings
event: rag      → {"chunks": [...]}         # Retrieved RAG context
event: done     → {"session_id": "..."}     # Stream complete
event: error    → {"message": "..."}        # Error occurred
```

## Project Structure

```
backend/              # FastAPI backend
  app/
    auth/             # Supabase Auth wrapper (signup, login, JWT validation)
    admin/            # Admin controls (users, AI config, preview, analytics)
    migrations/       # Migration sessions, CRUD, SSE streaming
    agent/            # AI agent (Claude client, prompts, parsers, vision, context)
    detection/        # Two-tier auto-detection (heuristic regex + AI fallback)
    memory/           # User preferences (regex + AI extraction, CRUD)
    rag/              # RAG system (Voyage AI embeddings, format-aware chunking, pgvector search)
    uploads/          # Supabase Storage file uploads
    common/           # Shared utilities (Supabase client, exceptions)
frontend/             # React + Vite + TypeScript + Tailwind
  src/
    api/              # API clients (auth, migrations, detection, preferences, rag, admin)
    auth/             # Auth provider, protected routes, login/signup pages
    pages/            # Dashboard, NewMigration, MigrationDetail, History, Preferences, admin/*
    components/       # ChatPanel, CodeEditor, YamlPreview, FileUploader, DetectionBadge, etc.
    hooks/            # useSSE, useAuth, useMigration
    lib/              # Supabase client, utilities
supabase/
  migrations/         # SQL migrations (001-005: schema, detection, preferences, RAG/pgvector, AI config)
```

## Database

Uses Supabase PostgreSQL with pgvector extension. Key tables:

- **user_profiles** - User accounts with role-based access (user/admin)
- **migration_sessions** - Pipeline migration sessions with auto-detection metadata
- **messages** - Conversation history per session
- **generated_workflows** - Generated GitHub Actions YAML outputs
- **user_preferences** - Learned user preferences with source tracking
- **documents / document_chunks** - RAG documents with vector embeddings (`vector(1024)`)
- **ai_config / rag_config** - Admin-configurable AI and RAG parameters
- **uploads** - File metadata for Supabase Storage
- **usage_logs** - Token usage tracking per request

All tables have Row Level Security (RLS) enabled. Secret key is used on the backend (bypasses RLS), publishable key on the frontend (respects RLS).
