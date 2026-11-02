"""FastAPI application entry point."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai.repository import get_ai_repo
from app.config import settings
from app.db import SessionLocal
from app.deps import get_db
from app.routers import ai, resumes
from app.routers import admin, applications, auth, bi, candidates, jobs, saved_jobs
from app.services.ai_repo import SqlAIRepository


def _configure_tfidf() -> None:
    """Fit M1 IDF once from the current open-job corpus."""
    try:
        with SessionLocal() as db:
            from app.services.ai_index import fit_open_job_corpus
            fit_open_job_corpus(db, force=True)
    except Exception:
        # A fresh database has no tables until Alembic is run by the container entrypoint.
        return


@asynccontextmanager
async def lifespan(app: FastAPI):
    _configure_tfidf()
    yield


app = FastAPI(title="SmartCareer API", version="1.0.0", description="API tìm việc, ứng tuyển, AI matching và BI.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=list(settings.cors_origins), allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


def _ai_repo(db=Depends(get_db)):
    return SqlAIRepository(db)


app.dependency_overrides[get_ai_repo] = _ai_repo
for router in (auth.router, candidates.router, jobs.router, applications.router, saved_jobs.router, admin.router, bi.router, ai.router, resumes.router):
    app.include_router(router, prefix="/api")


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}
