.PHONY: help dev start start-dev stop logs test lint format clean install pre-commit-install worker migrate revision upgrade

# Default environment: activate if .venv exists
SHELL      := /bin/bash
ACTIVATE   := $(shell if [ -d .venv ]; then echo "source .venv/bin/activate && "; fi)

help:
	@echo "Available commands:"
	@echo "  install             Install dependencies using uv (preferred) or pip."
	@echo "  dev                 Start all services (API, worker, DBs) using Docker Compose."
	@echo "  start               Start API server (production mode, needs build)."
	@echo "  start-dev           Start API server with hot-reloading."
	@echo "  worker              Start the Celery worker process."
	@echo "  stop                Stop all services started with 'make dev'."
	@echo "  logs                Follow logs for all services or a specific one (e.g., make logs s=api)."
	@echo "  test                Run pytest tests."
	@echo "  lint                Run linters (ruff, mypy, black, isort checks)."
	@echo "  format              Format code using ruff --fix, black, and isort."
	@echo "  clean               Remove cache files and build artifacts."
	@echo "  pre-commit-install  Install pre-commit hooks."
	@echo "  migrate             Apply database migrations (run 'make revision' first)."
	@echo "  revision            Generate a new database migration script."
	@echo "  upgrade             Alias for migrate."

install:
	@if command -v uv &> /dev/null; then \
		echo "Installing dependencies using uv..."; \
		$(ACTIVATE)uv pip install -e ".[dev]"; \
	else \
		echo "uv not found. Installing dependencies using pip..."; \
		$(ACTIVATE)pip install -e ".[dev]"; \
	fi

dev:
	@echo "Starting development environment with Docker Compose..."
	docker compose up --build -d
	@make logs

start:
	@echo "Starting API server (production mode)..."
	$(ACTIVATE)uvicorn app.main:app --host 0.0.0.0 --port 8000

start-dev:
	@echo "Starting API server with hot-reloading..."
	$(ACTIVATE)uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	@echo "Starting Celery worker..."
	$(ACTIVATE)python -m celery -A app.tasks.celery_app worker --loglevel=INFO

stop:
	@echo "Stopping Docker Compose services..."
	docker compose down

logs:
	@echo "Following logs (Ctrl+C to stop)... Use 'make logs s=<service>' for specific service."
	docker compose logs -f $(s)

test:
	@echo "Running tests..."
	$(ACTIVATE)pytest

lint:
	@echo "Running linters..."
	$(ACTIVATE)ruff check .
	$(ACTIVATE)mypy .
	$(ACTIVATE)black --check .
	$(ACTIVATE)isort --check-only .

format:
	@echo "Formatting code..."
	$(ACTIVATE)ruff check . --fix
	$(ACTIVATE)black .
	$(ACTIVATE)isort .

clean:
	@echo "Cleaning up cache and build artifacts..."
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache .coverage build dist *.egg-info htmlcov

pre-commit-install:
	@echo "Installing pre-commit hooks..."
	$(ACTIVATE)pre-commit install

# --- Database Migrations (Alembic) --- 
# Ensure ALEMBIC_CONFIG is set if your alembic.ini is not in the root
# export ALEMBIC_CONFIG=app/db/migrations/alembic.ini

revision:
	@echo "Generating new Alembic revision..."
	$(ACTIVATE)alembic revision --autogenerate -m "New migration"

migrate:
	@echo "Applying Alembic migrations..."
	$(ACTIVATE)alembic upgrade head

upgrade: migrate
