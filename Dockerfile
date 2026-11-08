# ForgeGuard API image: Python + torch + the tesseract binary (shelled out to
# directly by ocr_validation/engine.py, no Python OCR wrapper needed).
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ api/
COPY tamper_localisation/ tamper_localisation/
COPY signature_verification/ signature_verification/
COPY ocr_validation/ ocr_validation/
COPY anomaly_detection/ anomaly_detection/
COPY fusion/ fusion/
COPY ledger/ ledger/
COPY tamper_checkpoint.pt signature_checkpoint.pt anomaly_checkpoint.pt ./

# Render (and most PaaS) inject $PORT; default to 8000 for local `docker run`.
ENV PORT=8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT}"]
