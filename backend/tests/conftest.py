import os

# Test không tải model embedding thật; phải đặt trước khi nạp app.ai.embedder
os.environ.setdefault("EMBEDDER", "hash")
os.environ.setdefault("JWT_SECRET", "test-secret-test-secret-test-secret-32b")
os.environ.setdefault("BCRYPT_ROUNDS", "4")
