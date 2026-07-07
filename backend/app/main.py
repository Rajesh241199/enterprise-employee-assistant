from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import admin, auth, chat, departments, documents, events, poc
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.db.session import check_postgres_connection
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.rag.retrieval import check_qdrant_connection


def parse_cors_origins() -> list[str]:
    return [
        origin.strip()
        for origin in settings.cors_allowed_origins.split(",")
        if origin.strip()
    ]


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production-style internal employee knowledge assistant using Advanced RAG.",
    debug=settings.app_debug,
)


register_exception_handlers(app)


app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Request-ID",
    ],
)


app.add_middleware(SecurityHeadersMiddleware)


app.add_middleware(
    RateLimitMiddleware,
    default_limit=settings.rate_limit_requests,
    default_window_seconds=settings.rate_limit_window_seconds,
    login_limit=settings.login_rate_limit_requests,
    login_window_seconds=settings.login_rate_limit_window_seconds,
    max_request_body_bytes=settings.max_request_body_bytes,
)


app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(documents.router, prefix="/api", tags=["Documents"])
app.include_router(admin.router, prefix="/api", tags=["Admin Access Control"])
app.include_router(chat.router, prefix="/api", tags=["Chat Retrieval"])
app.include_router(departments.router, prefix="/api", tags=["Departments"])
app.include_router(events.router, prefix="/api", tags=["Events and Holidays"])
app.include_router(poc.router, prefix="/api", tags=["POC Lookup"])


@app.get("/")
def root():
    return {
        "message": "Enterprise Employee Knowledge Assistant API",
        "status": "running",
        "environment": settings.app_env,
    }


@app.get("/health")
def health_check():
    """
    Lightweight liveness check.

    This confirms the API process is running.
    It does not fail if external dependencies are unavailable.
    """
    return {
        "status": "ok",
        "app": settings.app_name,
        "environment": settings.app_env,
    }


@app.get("/ready")
def readiness_check():
    """
    Readiness check.

    This confirms whether required backend dependencies are reachable.
    """
    postgres_ok = check_postgres_connection()
    qdrant_ok = check_qdrant_connection()

    overall_status = "ok" if postgres_ok and qdrant_ok else "degraded"

    return {
        "status": overall_status,
        "app": settings.app_name,
        "environment": settings.app_env,
        "services": {
            "postgres": "ok" if postgres_ok else "error",
            "qdrant": "ok" if qdrant_ok else "error",
        },
    }