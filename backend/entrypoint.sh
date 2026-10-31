#!/bin/sh
set -e
# Tạo/cập nhật schema và view BI, nạp dữ liệu demo (bỏ qua nếu đã có), rồi chạy API.
alembic upgrade head
if [ "${SEED_ON_START:-1}" = "1" ]; then
    python -m seed.load_seed
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
