# WriteScore Container Image
# Multi-stage build for smaller final image

# Build stage - install dependencies and download models
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast package management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Create virtual environment and install package
RUN uv venv /app/.venv && \
    . /app/.venv/bin/activate && \
    uv pip install . && \
    python -m spacy download en_core_web_sm

# Download NLTK data
RUN . /app/.venv/bin/activate && \
    python -c "import nltk; nltk.download('punkt', quiet=True); nltk.download('punkt_tab', quiet=True); nltk.download('averaged_perceptron_tagger', quiet=True); nltk.download('averaged_perceptron_tagger_eng', quiet=True)"

# Pre-download transformer models (cached in image)
RUN . /app/.venv/bin/activate && \
    python -c "from transformers import pipeline; pipeline('sentiment-analysis', model='distilbert-base-uncased-finetuned-sst-2-english')"

# Runtime stage - minimal image
FROM python:3.12-slim AS runtime

WORKDIR /work

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy NLTK data
COPY --from=builder /root/nltk_data /root/nltk_data

# Copy HuggingFace cache (transformer models)
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Set PATH to use virtual environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Default entrypoint
ENTRYPOINT ["writescore"]
CMD ["--help"]

# Labels for container registries
LABEL org.opencontainers.image.title="WriteScore"
LABEL org.opencontainers.image.description="AI writing pattern analysis and scoring tool"
LABEL org.opencontainers.image.source="https://github.com/BOHICA-LABS/writescore"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.vendor="BOHICA Labs"
