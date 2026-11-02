FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    EMBEDDER=st \
    MODELS_DIR=/app/backend/models_store

WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev curl git && rm -rf /var/lib/apt/lists/*
COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip && \
    python -m pip install torch --index-url https://download.pytorch.org/whl/cpu && \
    python -m pip install -r /app/backend/requirements.txt

COPY backend /app/backend
COPY notebooks /app/notebooks
COPY bi /app/bi
WORKDIR /app/backend
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')"
ENV HF_HUB_OFFLINE=1
RUN python -m pytest /app/backend/tests -q

EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
