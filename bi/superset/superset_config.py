"""Apache Superset settings for local embedded dashboards."""
import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-this-superset-secret")
SQLALCHEMY_DATABASE_URI = os.environ["SQLALCHEMY_DATABASE_URI"]
FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}
GUEST_ROLE_NAME = "Public"
# Người xem nhúng (guest token) dùng role Public; cho role này quyền đọc dashboard/biểu đồ/dataset như Gamma
# (không có thì Superset trả 403 cho /api/v1/dashboard/<id>). Dữ liệu vẫn bị giới hạn bởi RLS trong guest token.
PUBLIC_ROLE_LIKE = "Gamma"
GUEST_TOKEN_JWT_SECRET = os.environ.get("GUEST_TOKEN_JWT_SECRET", "")
GUEST_TOKEN_JWT_ALGO = "HS256"
GUEST_TOKEN_JWT_EXP_SECONDS = 300
TALISMAN_ENABLED = False
ENABLE_CORS = True
CORS_OPTIONS = {
    "supports_credentials": True,
    "allow_headers": ["*"],
    "resources": ["/*"],
    "origins": ["http://localhost:5173", "http://localhost:8080"],
}
HTTP_HEADERS = {"X-Frame-Options": "ALLOWALL"}
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = False
WTF_CSRF_ENABLED = True
