"""Cấu hình Superset để nhúng dashboard vào ứng dụng bằng guest token (môi trường demo, KHÔNG dùng nguyên cho production)."""
import os

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]
SQLALCHEMY_DATABASE_URI = os.environ["SUPERSET_METADATA_URI"]  # postgresql+psycopg2://…/superset_meta

FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}

# Guest token: người xem nhúng dùng role này; PUBLIC_ROLE_LIKE cấp cho Public quyền đọc như Gamma
GUEST_ROLE_NAME = "Public"
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_TOKEN_JWT_SECRET = os.environ["GUEST_TOKEN_JWT_SECRET"]
GUEST_TOKEN_JWT_EXP_SECONDS = 600

# Cho phép trình duyệt tải dashboard trong iframe của ứng dụng (5173 khi dev, 8080 khi chạy qua nginx)
TALISMAN_ENABLED = False
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["*"],
    "origins": [o for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if o],
}
# Backend gọi REST API bằng Bearer token nên tắt CSRF cho môi trường demo
WTF_CSRF_ENABLED = False
SESSION_COOKIE_SAMESITE = "None"
SESSION_COOKIE_SECURE = False
