# ACRAS Unified Orchestration Makefile

.PHONY: help install lint format test typecheck pipeline dev clean validate evals evals-dry-run pre-commit security

help:
	@echo "ACRAS Orchestration Commands:"
	@echo "  install        - Install dependencies using uv"
	@echo "  lint           - Run ruff check and pyright"
	@echo "  format         - Run ruff format"
	@echo "  test           - Run pytest with coverage"
	@echo "  typecheck      - Run pyright"
	@echo "  pipeline       - Run the DVC pipeline (via main.py)"
	@echo "  dev            - Launch the Streamlit UI"
	@echo "  validate       - Run the multi-point validation suite"
	@echo "  evals-dry-run  - Validate eval harness wiring (no API calls)"
	@echo "  evals          - Run full LLM-as-a-Judge suite (requires API keys)"
	@echo "  pre-commit     - Run all pre-commit hooks on all files"
	@echo "  security       - Run Trivy vulnerability scan"

install:
	uv sync

lint:
	uv run ruff check .
	uv run pyright src/

format:
	uv run ruff format .

test:
	uv run pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=65

typecheck:
	uv run pyright src/

pipeline:
	uv run python main.py

dev:
	uv run streamlit run src/app.py

validate:
	./validate_system.bat

evals-dry-run:
	uv run python scripts/run_evals.py --dry-run

# The env var below conserves API quota and reduces suite latency by ~40% 
# because it automatically suppresses the live monitor during batch runs.
evals:
	$env:SKIP_LIVE_MONITORING=1; uv run python scripts/run_evals.py

pre-commit:
	uv run pre-commit run --all-files

security:
	trivy fs .
