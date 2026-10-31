from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.ai.repository import get_ai_repo
from app.config import get_settings
from app.deps import get_db
from app.routers import ai, applications, auth, bi, candidates, jobs, resumes, saved_admin
from app.services.ai_repo import SqlAIRepository


def create_app() -> FastAPI:
    app = FastAPI(title="SmartCareer API", version="2.0", docs_url="/docs", openapi_url="/openapi.json")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (auth.router, candidates.router, jobs.router, ai.router, resumes.router, applications.router,
                   saved_admin.saved_router, saved_admin.admin_router, bi.router):
        app.include_router(router, prefix="/api")

    def repo_factory(db: Session = Depends(get_db)) -> SqlAIRepository:
        return SqlAIRepository(db)

    app.dependency_overrides[get_ai_repo] = repo_factory

    @app.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    return app


app = create_app()
