FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install CPU-only PyTorch first to avoid heavy CUDA/NVIDIA packages.
RUN python -m pip install --upgrade pip && \
    pip install torch==2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu && \
    pip install -r requirements.txt

COPY app ./app
COPY evals ./evals
COPY scripts ./scripts

RUN mkdir -p logs storage/uploads storage/quarantine evals/reports

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=90s --retries=3 \
    CMD curl -f http://127.0.0.1:8000/health || exit 1

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]