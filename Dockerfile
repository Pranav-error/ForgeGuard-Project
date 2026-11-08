# Multi-stage: build the React frontend, then the Python API image that serves it.

FROM node:20-slim AS frontend-builder
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# ForgeGuard API image: Python + torch + the tesseract binary (shelled out to
# directly by ocr_validation/engine.py, no Python OCR wrapper needed).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
# CPU-only torch wheel: plain `pip install torch` on Linux pulls the full CUDA runtime
# (cudnn/nccl/cusparselt, ~1.5GB extra) even though this service only ever runs on CPU
# (NFR-2) -- confirmed live, it timed out a build entirely downloading GPU deps nothing
# here will ever use. The CPU wheel index skips all of that.
RUN pip install --no-cache-dir --timeout 180 torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install --no-cache-dir --timeout 180 -r requirements.txt

COPY api/ api/
COPY tamper_localisation/ tamper_localisation/
COPY signature_verification/ signature_verification/
COPY ocr_validation/ ocr_validation/
COPY anomaly_detection/ anomaly_detection/
COPY fusion/ fusion/
COPY ledger/ ledger/
COPY tamper_checkpoint.pt signature_checkpoint.pt anomaly_checkpoint.pt ./
COPY --from=frontend-builder /web/dist web/dist

# Render (and most PaaS) inject $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
