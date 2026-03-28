# Architecture

Technical overview of the AI CI/CD Migration Agent.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│              React + Vite + TypeScript + Tailwind                │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────────┐    │
│  │  Login /  │ │   New    │ │Migration │ │  Admin Panel    │    │
│  │  Signup   │ │Migration │ │  Detail  │ │ (AI/RAG/Users)  │    │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───────┬─────────┘    │
│       │             │            │                │              │
│  ┌────┴─────────────┴────────────┴────────────────┴──────────┐  │
│  │  Supabase Auth (direct)  │  API Client (JWT in header)    │  │
│  └──────────┬───────────────┴───────────────┬────────────────┘  │
└─────────────┼───────────────────────────────┼───────────────────┘
              │                               │
   Supabase Auth API               HTTP + SSE (port 8000)
              │                               │
              ▼                               ▼
┌─────────────────────┐   ┌──────────────────────────────────────┐
│   Supabase Cloud    │   │            BACKEND                    │
│                     │   │       FastAPI + Uvicorn                │
│  ┌───────────────┐  │   │                                       │
│  │  Auth Service  │  │   │  ┌─────────────────────────────────┐ │
│  │  (JWT issuer)  │◄─┼───┼──┤  dependencies.py                │ │
│  └───────────────┘  │   │  │  JWT validation via get_user()   │ │
│                     │   │  └─────────────────────────────────┘ │
│  ┌───────────────┐  │   │                                       │
│  │   Storage     │  │   │  ┌────────┐ ┌────────┐ ┌──────────┐ │
│  │  (file blobs) │◄─┼───┼──┤ auth/  │ │ admin/ │ │uploads/  │ │
│  └───────────────┘  │   │  └────────┘ └────────┘ └──────────┘ │
│                     │   │  ┌────────────┐ ┌──────────────────┐ │
│  ┌───────────────┐  │   │  │ migrations/│ │   detection/     │ │
│  │  PostgreSQL   │  │   │  │ (SSE)      │ │ (heuristic + AI) │ │
│  │  + pgvector   │◄─┼───┼──┤            │ └──────────────────┘ │
│  └───────────────┘  │   │  └────────────┘                      │
│                     │   │  ┌────────┐ ┌──────────────────────┐ │
└─────────────────────┘   │  │memory/ │ │        rag/          │ │
                          │  │(prefs) │ │ (embed + retrieve)   │ │
                          │  └────────┘ └──────────┬───────────┘ │
                          │                        │              │
                          │  ┌─────────────────────┴───────────┐ │
                          │  │          agent/                  │ │
                          │  │  client.py  (Claude streaming)   │ │
                          │  │  prompts.py (system prompts)     │ │
                          │  │  prompt_builder.py (assembler)   │ │
                          │  │  parsers.py (YAML extraction)    │ │
                          │  │  vision.py  (image processing)   │ │
                          │  │  context.py (sliding window)     │ │
                          │  └──────┬──────────────┬───────────┘ │
                          └─────────┼──────────────┼─────────────┘
                                    │              │
                                    ▼              ▼
                          ┌──────────────┐ ┌──────────────┐
                          │  Claude API  │ │  Voyage AI   │
                          │  (Anthropic) │ │ (embeddings) │
                          │              │ │              │
                          │  Sonnet:     │ │  voyage-3.5  │
                          │   migration  │ │  1024 dims   │
                          │  Haiku:      │ │              │
                          │   detection  │ │              │
                          └──────────────┘ └──────────────┘
```

## Request Flows

### Authentication Flow

```
1. User clicks Sign Up/Login on frontend
2. Frontend calls Supabase Auth directly (supabase.auth.signUp / signInWithPassword)
3. Supabase returns JWT access_token + refresh_token
4. Frontend stores tokens (Supabase JS SDK handles this automatically)
5. On signup, DB trigger auto-creates user_profiles row
6. For API calls: frontend sends JWT in Authorization header
7. Backend: dependencies.py extracts Bearer token
8. Backend: calls supabase.auth.get_user(token) to validate
9. Backend: looks up user_profiles for role + is_active check
10. Request proceeds or returns 401/403
```

### Migration Chat Flow (SSE Streaming)

```
1. User sends message via POST /api/migrations/{id}/messages
2. Backend saves user message to DB
3. If upload_ids provided, fetches image bytes from Supabase Storage
4. RAG service retrieves relevant document chunks:
   a. Generate query embedding (Voyage AI, input_type="query")
   b. Call match_document_chunks() RPC (pgvector cosine similarity)
   c. Filter by platform + doc_type, return top-k above threshold
5. Prompt builder assembles system prompt:
   ┌──────────────────────────────┐
   │ Base prompt (migration rules)│
   │ + Source context (TC/Jenkins) │
   │ + User preferences (memory)  │
   │ + RAG context (similar docs)  │
   └──────────────────────────────┘
6. Conversation history loaded (sliding window of last 20 messages)
7. Claude API called with streaming enabled
8. SSE events emitted as response streams:
   - event: rag     → retrieved context info
   - event: token   → streaming text chunks
   - event: yaml    → extracted GitHub Actions workflow
   - event: note    → warnings and migration notes
   - event: done    → stream complete
   - event: error   → error occurred
9. Full response saved to messages table
10. Generated YAML saved to generated_workflows table
11. Token usage logged to usage_logs table
```

### Auto-Detection Flow

```
1. Content submitted via POST /api/detect or during session creation
2. Tier 1 — Heuristic (no API cost):
   a. Score content against regex patterns for each platform/format
   b. Each pattern has a weight (0.0-1.0)
   c. Sum weights of matched patterns, cap at 1.0
   d. Detect config type: shared_library / complete_pipeline / fragment
   e. Fragment detection: match inner constructs, suppress if top-level wrapper found
   f. If combined confidence >= 0.7 → return result
3. Tier 2 — AI Fallback (low confidence):
   a. Send first 2000 chars to Claude Haiku (cheapest model)
   b. Request structured JSON classification
   c. Parse response, return with method="ai"
   d. If AI fails, return best heuristic guess
```

## Backend Module Map

```
backend/app/
├── main.py              FastAPI app, CORS, router registration, health check
├── config.py            Pydantic Settings (loads .env)
├── dependencies.py      get_current_user (JWT), require_admin (role check)
│
├── auth/                Supabase Auth wrapper
│   ├── router.py        POST /signup, /login, /refresh, GET /me
│   ├── service.py       Sign up, sign in, refresh, get user
│   └── models.py        Request/response schemas
│
├── admin/               Admin-only operations
│   ├── router.py        Users, AI config, preview, analytics
│   ├── service.py       User management, config CRUD, usage stats
│   └── models.py        Admin schemas
│
├── migrations/          Migration sessions + AI chat
│   ├── router.py        Session CRUD, SSE message endpoint
│   ├── service.py       Session management, stream_ai_response()
│   └── models.py        Session/message schemas
│
├── agent/               Claude AI integration
│   ├── client.py        Anthropic SDK wrapper, config cache (5min TTL)
│   ├── prompts.py       Base + TeamCity + Jenkins system prompts
│   ├── prompt_builder.py Assembles: base + source + preferences + RAG
│   ├── parsers.py       Extract YAML blocks, warnings, notes from output
│   ├── vision.py        Image resize + base64 for Claude vision API
│   └── context.py       Sliding window (last 20 messages) + summary
│
├── detection/           Pipeline auto-detection
│   ├── router.py        Detect, override, confirm endpoints
│   ├── service.py       Tier 1 heuristic + Tier 2 AI fallback
│   └── patterns.py      Regex patterns with weights per platform/format
│
├── memory/              User preference learning
│   ├── router.py        Preference CRUD + AI extraction trigger
│   ├── service.py       Regex extraction, AI extraction, upsert
│   └── models.py        Preference schemas
│
├── rag/                 Retrieval-Augmented Generation
│   ├── router.py        Document CRUD, search, config endpoints
│   ├── service.py       Ingest (chunk + embed + store), retrieve (search + filter)
│   ├── chunking.py      Format-aware chunkers (Jenkins, TeamCity, XML, Markdown, Fallback)
│   ├── embedding.py     Voyage AI client (document vs query input types)
│   └── models.py        Document/search schemas
│
├── uploads/             File management
│   ├── router.py        Upload file, get signed URL
│   └── service.py       Supabase Storage integration
│
└── common/              Shared utilities
    ├── supabase.py      Singleton clients (publishable + secret key)
    └── exceptions.py    HTTP exception classes
```

## Prompt Architecture

The system prompt is assembled in layers by `agent/prompt_builder.py`:

```
┌─────────────────────────────────────────────────────────┐
│                    SYSTEM PROMPT                         │
│                                                          │
│  Layer 1: Base Prompt                                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ You are a CI/CD migration specialist...            │ │
│  │ Rules for GitHub Actions output format, YAML       │ │
│  │ structure, naming conventions, best practices      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Layer 2: Source-Specific Context                        │
│  ┌────────────────────────────────────────────────────┐ │
│  │ TeamCity: Kotlin DSL mappings, buildType → job,    │ │
│  │   step types, VCS triggers, artifact rules         │ │
│  │ — OR —                                             │ │
│  │ Jenkins: Groovy → YAML mappings, agent → runs-on,  │ │
│  │   stage → job, plugin equivalents, shared libs     │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Layer 3: User Preferences (from memory)                │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ## User Preferences (from past sessions)           │ │
│  │ - runner_image/default_runner: ubuntu-22.04        │ │
│  │ - build_strategy/prefer_matrix: true               │ │
│  │ - tooling/package_manager: pnpm                    │ │
│  │ Honor unless conflicting with specific request.    │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Layer 4: RAG Context                                    │
│  ┌────────────────────────────────────────────────────┐ │
│  │ ## Similar Past Migrations                         │ │
│  │ [chunks from previous successful migrations]       │ │
│  │                                                    │ │
│  │ ## Relevant Documentation                          │ │
│  │ [chunks from reference docs / GitHub Actions docs] │ │
│  └────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## RAG Pipeline

### Ingestion (document upload or auto-ingest)

```
Content → Format Detection → Chunker Selection → Chunking → Embedding → Storage

Chunkers:
  JenkinsGroovyChunker   → splits on stage boundaries, prepends pipeline header
  TeamCityKotlinChunker  → splits on buildType/object/vcsRoot boundaries
  TeamCityXMLChunker     → splits on XML element boundaries
  MarkdownDocChunker     → splits on heading boundaries
  FallbackChunker        → token-based sliding window (512 tokens, 64 overlap)

Embedding:
  Voyage AI voyage-3.5 model, 1024 dimensions
  input_type="document" for ingestion
  Batch processing: 128 chunks per API call
```

### Retrieval (during migration chat)

```
Query → Embedding → pgvector Similarity Search → Filter → Return

Embedding:
  Voyage AI voyage-3.5, input_type="query" (optimized for search)

Search:
  match_document_chunks() PostgreSQL function
  Cosine similarity via pgvector IVFFlat index
  Filters: doc_type, source_platform
  Default: top 5 chunks above 0.75 similarity threshold

All parameters configurable by admin via RAG settings UI.
```

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Sync Supabase client | Supabase Python SDK is synchronous. Wrapped in sync service methods to avoid blocking event loop issues. |
| Singleton pattern for clients | Supabase and Claude clients reuse connections. Global singletons with lazy initialization. |
| Config cache with 5-min TTL | AI config loaded from DB; cached to avoid DB call per request. TTL ensures admin changes propagate within 5 minutes. |
| Voyage AI for embeddings | Anthropic's official embedding partner. Supports document vs query input types for better retrieval. |
| Format-aware chunking | Naive token splitting breaks semantic boundaries. Format-specific chunkers preserve pipeline structure (stages, buildTypes, XML elements). |
| Heuristic-first detection | Regex patterns are free and fast. AI fallback only when confidence < 0.7, using cheapest model (Haiku). |
| SSE for streaming | Server-Sent Events are simpler than WebSockets for one-directional streaming. Works with standard HTTP. |
| Layered system prompt | Separates concerns: base rules, source knowledge, user context, RAG context. Each layer is independently testable. |
| RLS on all tables | Defense in depth. Even if backend has a bug, database policies prevent unauthorized access. |

---

**Next:** [Local Setup](setup-local.md) | [Docker Setup](setup-docker.md) | [Supabase Setup](supabase-setup.md)
