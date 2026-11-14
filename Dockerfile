# =====================================================================
# ViTrueVoice Dockerfile - High-Performance Audio Anti-Spoofing Container
# Tech Stack: Python 3.12, PyTorch 2.6, torchaudio, FFmpeg (in-memory)
# =====================================================================

FROM python:3.12-slim

# Labels & Metadata
LABEL maintainer="Nguyen Thanh Tai <2380601959@hutech.edu.vn>"
LABEL project="ViTrueVoice"
LABEL description="Vietnamese compressed telephony voice anti-spoofing detection system"

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    DEVICE=cpu \
    HOME=/home/appuser \
    HF_HOME=/home/appuser/.cache/huggingface \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies: FFmpeg is mandatory for in-memory audio decoding
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user with home directory for enterprise container security (AWS Security / CIS Docker Benchmark)
RUN groupadd -r appgroup && useradd -m -r -g appgroup -u 1000 -d /home/appuser appuser

WORKDIR /app

# Install Python dependencies first for caching layers
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and scripts
COPY src/ /app/src/
COPY scripts/ /app/scripts/

# Create directories for models, Hugging Face cache, data, external, and logs with non-root ownership
RUN mkdir -p /home/appuser/.cache/huggingface /app/out /app/benchmarks /app/data /app/external && \
    chown -R appuser:appgroup /home/appuser /app

# Switch to non-root user
USER appuser

# Expose FastAPI service port
EXPOSE 8000

# Container Healthcheck via /health endpoint (allow 60s for model loading on cold start)
HEALTHCHECK --interval=20s --timeout=5s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command: Start FastAPI ASGI server
CMD ["uvicorn", "src.app.server:app", "--host", "0.0.0.0", "--port", "8000"]
