# ============================================================
# Stage 1: Dependency installer using the official uv image
# ============================================================
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim AS builder

WORKDIR /app

# Enable uv's bytecode compilation and frozen lockfile mode for reproducible builds
ENV UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1

# Install system dependencies required for some Python packages (e.g., scikit-learn)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# --- Layer cache optimization ---
# Copy ONLY the dependency manifest first. This layer is cached and skipped
# on rebuilds as long as pyproject.toml has not changed.
COPY pyproject.toml .

# Install all project dependencies into /app/.venv (excluding dev extras)
RUN uv sync --no-dev --no-install-project

# ============================================================
# Stage 2: Lean runtime image
# ============================================================
FROM python:3.10-slim AS runtime

WORKDIR /app

# Python runtime best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"

# Install minimal runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Copy the pre-built virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy the application source code and required config
COPY src/ ./src/
COPY config/ ./config/
COPY pyproject.toml .

# Copy required model artifacts (must exist locally before building)
# These are produced by the DVC pipeline: uv run dvc repro
COPY artifacts/model_trainer/acras_rf_model.joblib ./artifacts/model_trainer/acras_rf_model.joblib
COPY artifacts/data_transformation/preprocessor.pkl ./artifacts/data_transformation/preprocessor.pkl
COPY artifacts/data_ingestion/val.csv ./artifacts/data_ingestion/val.csv

# Transfer ownership to the non-root user
RUN chown -R appuser:appuser /app
USER appuser

# Expose the FastAPI service port
EXPOSE 8000

# Health check for container orchestration (Kubernetes / Docker Compose)
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production entrypoint
CMD ["uvicorn", "src.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
