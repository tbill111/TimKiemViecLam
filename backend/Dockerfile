# Build từ thư mục gốc repo:  docker build -f backend/Dockerfile .
FROM python:3.11-slim

# WITH_ST=1: cài torch (CPU), sentence-transformers, underthesea và tải sẵn model để chạy offline (image lớn, ~2 GB).
# WITH_ST=0: chỉ cài phần nhẹ; tầng AI tự dùng HashingEmbedder (đủ chạy demo, KHÔNG dùng số liệu này để báo cáo).
ARG WITH_ST=1

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 HF_HOME=/opt/hf PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv/backend
COPY backend/requirements.txt ./
RUN pip install -r requirements.txt

RUN if [ "$WITH_ST" = "1" ]; then \
      pip install torch --index-url https://download.pytorch.org/whl/cpu \
      && pip install "sentence-transformers>=3.0" "underthesea>=6.8" \
      && python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')" ; \
    fi
ENV HF_HUB_OFFLINE=${WITH_ST}

COPY backend/ ./
COPY bi/views.sql /srv/bi/views.sql
RUN chmod +x entrypoint.sh

EXPOSE 8000
CMD ["./entrypoint.sh"]
