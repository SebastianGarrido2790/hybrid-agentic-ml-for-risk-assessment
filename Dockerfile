# ============================================================
# Stage 1: Dependency installer using the official uv image
# ============================================================
# Best Practice: Pin specific image versions (optionally with @sha256 digests) for reproducibility
FROM ghcr.io/astral-sh/uv:0.5.21-python3.10-bookworm-slim@sha256:f1f417f7663248888e223f03b070440375a2d64f7b494665487779774640960c AS builder

WORKDIR /app

# Enable uv's bytecode compilation and frozen lockfile mode for reproducible builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1

# Install system dependencies required for some Python packages (e.g., pycairo, scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libcairo2-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Layer cache optimization ---
# Copy ONLY the dependency manifests first. This layer is cached and skipped
# on rebuilds as long as pyproject.toml and uv.lock have not changed.
COPY pyproject.toml uv.lock ./

# Install all project dependencies into /app/.venv (excluding dev extras)
RUN uv sync --no-dev --no-install-project

# ============================================================
# Stage 2: Production-ready runtime image
# ============================================================
FROM python:3.10.16-slim-bookworm@sha256:85521e1026090f4a869811409f8992e07172ec43f497745778841050a4d65020 AS runtime

# Metadata labels for container orchestration and compliance
LABEL org.opencontainers.image.title="ACRAS - Agentic Credit Risk Assessment System" \
      org.opencontainers.image.description="Unified production image for the ACRAS Agent Cluster (FastAPI & Streamlit)" \
      org.opencontainers.image.version="2.2"
# Hardened Synthesis Version (Production Elite)

WORKDIR /app

# Python runtime best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install minimal runtime system dependencies (libcairo2 + pango for xhtml2pdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libcairo2 \
    libpangocairo-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root group and user for security
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /bin/bash appuser

# Ensure the appuser owns the workdir and create the logs/ directory which is required at runtime
RUN mkdir -p /app/logs && chown -R appuser:appuser /app

# Switch ownership using --chown during COPY to avoid creating bloated layers
COPY --chown=appuser:appuser --from=builder /app/.venv /app/.venv

# Copy the application source code and required config
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/
COPY --chown=appuser:appuser reports/ ./reports/
COPY --chown=appuser:appuser pyproject.toml uv.lock README.md ./

# Copy required model artifacts (must exist locally before building)
# These are produced by the DVC pipeline: uv run dvc repro
COPY --chown=appuser:appuser artifacts/ ./artifacts/

# Transfer execution to the non-root user
USER appuser

# Expose ports for both FastAPI (8000) and Streamlit (8501)
EXPOSE 8000 8501

# Health check for container orchestration (Kubernetes / Docker Compose)
# Note: In Compose, we override this for specific services
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || curl -f http://localhost:8501/_stcore/health || exit 1

# Default entrypoint (can be overridden in docker-compose.yaml)
# To run API: uvicorn src.app.main:app
# To run UI: streamlit run src/ui/app.py
ENTRYPOINT ["/app/.venv/bin/python", "-m"]
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
