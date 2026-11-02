"""Runtime configuration for the SmartCareer API."""
from __future__ import annotations

import os


class Settings:
    database_url: str = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://smartcareer:smartcareer@localhost:5432/smartcareer"
    )
    jwt_secret: str = os.getenv("JWT_SECRET", "development-only-change-me")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    default_model: str = os.getenv("DEFAULT_MODEL", "m3")
    cors_origins: tuple[str, ...] = ("http://localhost:5173", "http://localhost:8080")
    superset_url: str = os.getenv("SUPERSET_URL", "http://superset:8088")
    superset_public_url: str = os.getenv("SUPERSET_PUBLIC_URL", "http://localhost:8088")
    superset_username: str = os.getenv("SUPERSET_ADMIN_USER", "admin")
    superset_password: str = os.getenv("SUPERSET_ADMIN_PASSWORD", "")
    guest_token_secret: str = os.getenv("GUEST_TOKEN_JWT_SECRET", "")
    dashboard_id: str = os.getenv("SUPERSET_DASHBOARD_ID", "")
    funnel_dataset_id: str = os.getenv("SUPERSET_FUNNEL_DATASET_ID", "")
    funnel_stages_dataset_id: str = os.getenv("SUPERSET_FUNNEL_STAGES_DATASET_ID", "")


settings = Settings()
