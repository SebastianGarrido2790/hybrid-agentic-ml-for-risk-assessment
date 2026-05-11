# ACRAS Unified Orchestration Makefile

.PHONY: help install lint format test typecheck pipeline dev clean validate

help:
	@echo "ACRAS Orchestration Commands:"
	@echo "  install    - Install dependencies using uv"
	@echo "  lint       - Run ruff check and pyright"
	@echo "  format     - Run ruff format"
	@echo "  test       - Run pytest with coverage"
	@echo "  typecheck  - Run pyright"
	@echo "  pipeline   - Run the DVC pipeline (via main.py)"
	@echo "  dev        - Launch the Streamlit UI"
	@echo "  validate   - Run the multi-point validation suite"

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
