# Planet Earth - OpenAPI Ingestion & Vector Search

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-FastAPI-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

FastAPI service to ingest OpenAPI 3.x specifications, embed individual operations locally using Sentence Transformers, and provide semantic search capabilities via a self-hosted vector database (Chroma) and relational store (PostgreSQL).

Based on the requirements outlined in `instructions.md`.

## ✨ Features

*   **OpenAPI Ingestion**: Upload YAML/JSON specs via `POST /v1/schemas`.
*   **Local Embedding**: Uses `sentence-transformers/all-MiniLM-L6-v2` for embedding.
*   **Semantic Search**: Find relevant API endpoints via `POST /v1/search`.
*   **Delta Updates**: Handles re-ingestion of updated specifications.
*   **Relational & Vector Storage**: Uses PostgreSQL for metadata and Chroma for vectors.
*   **Background Processing**: Uses RQ (Redis Queue) for asynchronous ingestion.
*   **Dockerized**: Easy setup and deployment using Docker Compose.
*   **Tooling**: Includes `make` commands for development, testing, and linting.

## 🚀 Getting Started

### Prerequisites

*   [Docker](https://docs.docker.com/get-docker/) and Docker Compose
*   [uv](https://github.com/astral-sh/uv) (Python package installer/resolver, recommended)
*   Python 3.11+
*   `make`

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone <your-repo-url>
    cd earth-service
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    # Using uv (recommended)
    uv venv
    source .venv/bin/activate

    # Or using standard venv
    # python -m venv .venv
    # source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    uv pip install -e ".[dev]"
    # Or using pip
    # pip install -e ".[dev]"
    ```

4.  **Set up environment variables:**
    Copy the example `.env.example` file to `.env` and fill in the required values (Database URLs, secrets, etc.).
    ```bash
    cp .env.example .env
    # vim .env # or use your favorite editor
    ```

5.  **Start the development services:**
    This command will build the necessary Docker images (if they don't exist) and start the API server, worker, PostgreSQL, Redis, and ChromaDB containers.
    ```bash
    make dev
    ```
    The API will be available at `http://localhost:8000`.

## 🛠️ Development

*   **Run the API server with hot-reloading:**
    ```bash
    make start-dev
    # Or directly with uvicorn:
    # uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    ```
*   **Run the RQ worker:**
    Ensure Redis is running (`make dev` starts it).
    ```bash
    make worker
    # Or directly:
    # python -m app.tasks.ingest_worker
    ```
*   **Run tests:**
    ```bash
    make test
    ```
*   **Run linters & formatters:**
    ```bash
    make lint # Runs ruff, mypy, black (check), isort (check)
    make format # Runs ruff --fix, black, isort
    ```
*   **Run pre-commit checks (install hooks first):**
    ```bash
    pre-commit install
    pre-commit run --all-files
    ```
*   **Database Migrations (Alembic):**
    *(Setup required in `app/db/migrations/env.py` and `app/core/config.py`)*
    ```bash
    # Create a new migration script (after changing models)
    # alembic revision --autogenerate -m "Describe changes"

    # Apply migrations
    # alembic upgrade head
    ```

## 🐳 Docker

*   **Build images:** `docker compose build`
*   **Start services:** `docker compose up -d` (or `make dev`)
*   **Stop services:** `docker compose down`
*   **View logs:** `docker compose logs -f [service_name]` (e.g., `docker compose logs -f api`)

## ⚙️ Configuration

Configuration is managed via environment variables and Pydantic settings (`app/core/config.py`). See `.env.example` for available variables.

## API Endpoints

*   **Docs:** `http://localhost:8000/docs` (Swagger UI)
*   **Schema Upload:** `POST /v1/schemas`
*   **Search:** `POST /v1/search`
*   *(Other endpoints as defined in `app/api/v1/`)*

## Project Structure

```
app/
 ├─ api/                # FastAPI routers (v1, deps)
 ├─ core/               # Settings, logging, auth utils
 ├─ db/                 # DB session, migrations (Alembic)
 ├─ models/             # SQLModel ORM models
 ├─ services/           # Business logic (parser, embedder, vector_store)
 ├─ tasks/              # Background tasks (RQ worker)
 └─ main.py             # FastAPI app entrypoint
tests/                 # Pytest tests
.env.example           # Environment variable template
.gitignore
compose.yaml           # Docker Compose config
Dockerfile
instructions.md        # Original PRD
Makefile
pyproject.toml         # Project metadata & dependencies (uv/pip)
README.md
```

## Contributing

Please refer to the contribution guidelines if you wish to contribute.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (To be created).
