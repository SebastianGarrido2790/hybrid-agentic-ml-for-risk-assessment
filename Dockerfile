# ============================================================
# Stage 1: Dependency installer using the official uv image
# ============================================================
# Best Practice: Pin specific image versions (optionally with @sha256 digests) for reproducibility
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

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
# Stage 2: Lean runtime image
# ============================================================
FROM python:3.10-slim-bookworm AS runtime

# Metadata labels for container orchestration and compliance
LABEL org.opencontainers.image.title="ACRAS API Prediction Service" \
      org.opencontainers.image.description="FastAPI microservice for risk assessment" \
      org.opencontainers.image.version="1.0"

WORKDIR /app

# Python runtime best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install minimal runtime system dependencies (libcairo2 for xhtml2pdf)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libcairo2 \
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
COPY --chown=appuser:appuser pyproject.toml uv.lock ./

# Copy required model artifacts (must exist locally before building)
# These are produced by the DVC pipeline: uv run dvc repro
COPY --chown=appuser:appuser artifacts/model_trainer/acras_rf_model.joblib ./artifacts/model_trainer/acras_rf_model.joblib
COPY --chown=appuser:appuser artifacts/data_transformation/preprocessor.pkl ./artifacts/data_transformation/preprocessor.pkl
COPY --chown=appuser:appuser artifacts/data_ingestion/val.csv ./artifacts/data_ingestion/val.csv

# Transfer execution to the non-root user
USER appuser

# Expose the FastAPI service port
EXPOSE 8000

# Health check for container orchestration (Kubernetes / Docker Compose)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint
ENTRYPOINT ["/app/.venv/bin/python", "-m", "uvicorn", "src.app.main:app"]
CMD ["--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
