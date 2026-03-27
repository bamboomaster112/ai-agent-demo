# AI CI/CD Migration Agent

An AI-powered application that helps migrate CI/CD pipelines from **TeamCity** and **Jenkins** to **GitHub Actions**.

## Features

- **Auto-Detection**: Automatically identifies pipeline type (TeamCity/Jenkins), format (Kotlin DSL, XML, JSON, Groovy), and config type (shared library, complete pipeline, fragment)
- **AI-Powered Migration**: Chat-based interface with streaming responses powered by Claude (Anthropic)
- **Screenshot Analysis**: Upload screenshots of pipeline UIs for vision-based analysis
- **RAG Support**: Context-aware retrieval using past migrations and reference documentation
- **User Preferences/Memory**: Learns and remembers user preferences across sessions
- **Admin Controls**: Model selection, temperature, RAG parameters, user management, analytics

## Tech Stack

- **Backend**: Python FastAPI
- **Frontend**: React + Vite (TypeScript)
- **AI**: Claude API (Anthropic)
- **Database**: Supabase (PostgreSQL + pgvector + Auth + Storage)

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase project (or local Supabase via Docker)

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

Copy `.env.example` and fill in your values:

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OPENAI_API_KEY` - OpenAI API key (for embeddings)

## Project Structure

```
backend/          # FastAPI backend
  app/
    auth/         # Authentication
    admin/        # Admin controls
    migrations/   # Migration sessions & chat
    agent/        # AI agent (Claude integration)
    detection/    # Auto-detection engine
    memory/       # User preferences/memory
    rag/          # RAG system
    uploads/      # File uploads
frontend/         # React + Vite frontend
supabase/         # Database migrations
```
