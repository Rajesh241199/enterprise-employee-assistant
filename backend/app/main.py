from fastapi import FastAPI

from app.api import admin, auth, chat, departments, documents, events, poc
from app.core.config import settings
from app.db.session import check_postgres_connection
from app.rag.retrieval import check_qdrant_connection


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Production-style internal employee knowledge assistant using Advanced RAG."
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
        "status": "running"
    }


@app.get("/health")
def health_check():
    postgres_ok = check_postgres_connection()
    qdrant_ok = check_qdrant_connection()

    overall_status = "ok" if postgres_ok and qdrant_ok else "degraded"

    return {
        "status": overall_status,
        "app": settings.app_name,
        "environment": settings.app_env,
        "services": {
            "postgres": "ok" if postgres_ok else "error",
            "qdrant": "ok" if qdrant_ok else "error"
        }
    }