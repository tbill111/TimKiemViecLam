"""Cấu hình đọc từ biến môi trường (xem .env.example ở thư mục gốc)."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./smartcareer_dev.db"
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 12
    bcrypt_rounds: int = 12
    cors_origins: str = "http://localhost:5173,http://localhost:8080"
    default_model: str = "m3"

    # Superset (nhúng dashboard)
    superset_url: str = ""  # ví dụ http://superset:8088 (địa chỉ API nội bộ)
    superset_public_url: str = "http://localhost:8088"  # địa chỉ trình duyệt dùng để nhúng
    superset_admin_user: str = "admin"
    superset_admin_password: str = "admin"
    superset_dashboard_id: str = ""  # UUID nhúng của dashboard
    superset_rls_dataset_ids: str = ""  # id các dataset có cột company_id (v_funnel, v_funnel_stages), cách nhau dấu phẩy

    @property
    def rls_dataset_ids(self) -> list[int]:
        return [int(x) for x in self.superset_rls_dataset_ids.split(",") if x.strip()]

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
