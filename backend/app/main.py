from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown


app = FastAPI(
    title="AI CI/CD Migration Agent",
    description="Migrate TeamCity and Jenkins pipelines to GitHub Actions",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and register routers
from app.auth.router import router as auth_router
from app.admin.router import router as admin_router
from app.migrations.router import router as migrations_router
from app.detection.router import router as detection_router
from app.memory.router import router as memory_router
from app.rag.router import router as rag_router
from app.uploads.router import router as uploads_router

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
app.include_router(migrations_router, prefix="/api/migrations", tags=["migrations"])
app.include_router(detection_router, prefix="/api/detect", tags=["detection"])
app.include_router(memory_router, prefix="/api/users/me/preferences", tags=["memory"])
app.include_router(rag_router, prefix="/api/rag", tags=["rag"])
app.include_router(uploads_router, prefix="/api/uploads", tags=["uploads"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
