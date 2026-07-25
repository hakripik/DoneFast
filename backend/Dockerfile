# Study Assistant backend — FastAPI + PyMuPDF + ChromaDB + sentence-transformers.
#
# ANTHROPIC_API_KEY is never baked into this image. It's supplied at container
# start via docker-compose's `env_file`, reading from a local .env that is
# git-ignored and never copied into the build context (see .dockerignore).
FROM python:3.11-slim

WORKDIR /app

# build-essential covers the rare compiled wheel (e.g. some chromadb
# dependencies) without a prebuilt binary for the target platform.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# backend/uploads, backend/chroma_db, and backend/annotated are bind-mounted
# as volumes by docker-compose.yml — they intentionally don't exist in the
# image itself, so data survives container rebuilds/restarts.

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
