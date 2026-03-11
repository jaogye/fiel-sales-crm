"""
Field Sales CRM — FastAPI Application

AI-powered mobile CRM for field sales teams.
Runs on the owner's Windows laptop with SQLite.

Usage:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import router

logger = logging.getLogger(__name__)

_DEFAULT_SECRET = "change-this-to-a-random-string-in-production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup checks + table creation."""
    # Refuse to start in production with the default secret key
    if not settings.debug and settings.secret_key == _DEFAULT_SECRET:
        raise RuntimeError(
            "SECRET_KEY must be changed before running in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )
    if settings.secret_key == _DEFAULT_SECRET:
        logger.warning(
            "WARNING: Using the default SECRET_KEY. "
            "Generate a secure key before going to production: "
            "python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Field Sales CRM",
    description=(
        "AI-powered CRM for field sales teams. "
        "Automatically transcribes visit conversations and fills CRM fields."
    ),
    version="0.1.0",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# CORS — Bearer tokens are used, not cookies, so allow_credentials=False
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Include API routes
app.include_router(router)


@app.get("/", tags=["health"])
async def root():
    return {
        "app": "Field Sales CRM",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health", tags=["health"])
async def health_check():
    return {"status": "healthy"}
