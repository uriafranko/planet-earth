## Product Requirements – *OpenAPI Ingestion & Local Vector‑Search Service*

> **Audience:** Backend / AI engineers building and running the service locally or in‑house. The goal is to give you everything you need—code structure, tooling, and infra—to clone, `make dev`, and start hacking immediately.

---
### 1. TL;DR (Why This Exists)
We ingest **OpenAPI 3.x specs**, explode them into individual operations, embed each operation **locally** with a free, open‑source model, and store both vectors & metadata in a self‑hosted vector DB so we can:
1. Run semantic search ("Which API lets me *create an order*?")
2. Track provenance → every endpoint knows which spec version produced it.
3. Re‑ingest updated specs and *diff* changes without breaking referential links.

Everything runs in Docker and costs \$0 in SaaS fees.

---
### 2. Tech Stack (No Paid Vendors)
| Layer | Choice | Why |
|-------|--------|-----|
|Web framework|**FastAPI**| async, great DX, OpenAPI native |
|Task queue|**RQ** (Redis Queue) | simple, good enough for our async ingestion |
|Relational DB|**PostgreSQL 15**| referential integrity, cheap local |
|Vector DB|**Chroma** (SQLite/duckdb backend) | open‑source, disk‑based persistence |
|Embeddings|**Sentence‑Transformers `all‑MiniLM‑L6‑v2`** (≈384‑dim) | GPL‑friendly, <100 MB, runs CPU‑only |
|Infra|Docker Compose | one‑liner spin‑up |
|Lang|Python 3.11 | latest LTS |

> **NOTE**: You can swap Chroma for **FAISS** if you prefer—interface is abstracted.

---
### 3. High‑Level Architecture
```
┌──────────────┐     enqueue        ┌─────────────┐     insert        ┌─────────────┐
│  FastAPI     │ ───────────────▶ │  RQ Worker  │ ───────────────▶ │  Chroma DB  │
│  /schemas    │                   │  (parser)   │                   │  + Postgres │
└──────────────┘ ◀──── query ───── └─────────────┘ ◀──── meta ──────┘
```
* **FastAPI** exposes:
  * `POST /schemas` – upload YAML/JSON spec (≤5 MB)
  * `POST /search` – semantic search over endpoints
  * `GET /schemas/{id}/endpoints` – list raw endpoints for UI/CLI
* **Worker** does heavy lifting: parse → flatten → embed → store.
* **Chroma** keeps vectors; **Postgres** keeps relational truth.

---
### 4. Data Model
```sql
CREATE TABLE schemas (
  id UUID PRIMARY KEY,
  title TEXT,
  version TEXT,
  checksum TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE endpoints (
  id UUID PRIMARY KEY,
  schema_id UUID REFERENCES schemas(id) ON DELETE CASCADE,
  path TEXT,
  method TEXT,
  operation_id TEXT,
  hash TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX ux_schema_path_method ON endpoints(schema_id, path, method);
```

Vector store row keeps: `endpoint_id`, `embedding (vector<float32[384]>)`, plus lightweight metadata mirror (`path`, `method`, `schema_id`).

---
### 5. Detailed Functional Requirements
| # | Feature | Dev Notes |
|---|---------|-----------|
|F1|**Schema Upload**|Multipart or raw body; validate with `openapi‑schema‑validator`; immediately 202 + `schema_id`; push job to RQ|
|F2|**Parser**|Use `openapi‑spec‑validator` + `jsonref` to resolve `$ref`s; flatten each `path + method` into dict for embedding|
|F3|**Embedding Service**|Python module wrapping Sentence‑Transformers; batch size 64; cache on disk using `joblib`|
|F4|**Vector Persistence**|Abstract `VectorStore` interface; default Chroma (collection=`endpoints`); ID = `endpoint_id`|
|F5|**Semantic Search**|`POST /search` → embed query → `vector_store.similarity_search(k)` → join with Postgres for full payload|
|F6|**Delta Update**|On new spec upload with same checksum → 409; with different checksum but same `(title, version)` → mark endpoints diff; deleted endpoints soft‑deleted|
|F7|**Auth**|Optional for local; enable via `settings.ENABLE_AUTH`; JWT w/ HS256 secret in `.env`|
|F8|**Observability**|Log to stdout (json‑structured) + Prometheus `/metrics`; traces optional via OTLP exporter|

---
### 6. Non‑Functional Targets
* **Ingestion latency:** ≤3 s P95 for 1 MB spec on laptop (M1 / 8‑core CPU)
* **Search latency:** ≤100 ms P95 for `k=10` on 10k endpoints (CPU‑only)
* **Local footprint:** All containers <1 GB RAM each; embeddings model <100 MB

---
### 7. Dev Environment & Tooling
```
make dev        # boot postgres, redis, chroma, api, worker
make test       # run pytest w/ coverage
make lint       # ruff + mypy
make embed      # (re)embed all endpoints
```
* **Pre‑commit**: ruff, mypy, black (check only), isort.
* **.env**: holds DB URIs, `MODEL_NAME`, `CHROMA_PERSIST_DIR`.
* **Hot reload**: `uvicorn app.main:app --reload`.
* **Debugging**: VS Code devcontainer.json included.

---
### 8. Repo Layout
```
app/
 ├─ api/                # FastAPI routers
 │   ├─ v1/
 │   │   ├─ schemas.py   # upload endpoints
 │   │   ├─ search.py    # semantic search
 │   │   └─ management.py
 │   └─ deps.py
 ├─ core/               # settings, logging, auth utils
 ├─ db/
 │   ├─ session.py
 │   └─ migrations/
 ├─ models/             # SQLModel ORM models
 ├─ services/
 │   ├─ parser.py
 │   ├─ embedder.py
 │   └─ vector_store.py  # Chroma impl & interface
 ├─ tasks/
 │   └─ ingest_worker.py
 └─ tests/
Dockerfile
compose.yaml
pyproject.toml
README.md
```

---
### 9. Docker Compose Snippet
```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: secret
    ports: ["5432:5432"]
  redis:
    image: redis:7
    ports: ["6379:6379"]
  chroma:
    image: ghcr.io/chroma-core/chroma:latest
    volumes:
      - ./chroma_data:/chroma/.chroma/index
    ports: ["8001:8000"]
  api:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
    depends_on: [postgres, redis, chroma]
    ports: ["8000:8000"]
  worker:
    build: .
    command: python -m app.tasks.ingest_worker
    depends_on: [api]
```

---
### 10. Testing Strategy
* **Unit**: parser edge cases, embedder returns 384‑len vectors, vector_store upserts.
* **Integration**: spin‑up compose, upload sample spec, assert search hits.
* **E2E**: GitHub Action runs `make e2e` → behaves identical on PRs.

---
### 11. Rollout Plan
1. **Week 0** – scaffold repo + compose; run hello world.
2. **Week 1** – implement parser & DB models; store raw endpoints.
3. **Week 2** – embedder + vector store + search route.
4. **Week 3** – delta updates + auth + docs.
5. **Week 4** – tests, CI/CD, code freeze.

---
### 12. Risks & Mitigations
| Risk | Mitigation |
|------|-----------|
|CPU‑only embeddings slow on huge specs| Allow optional GPU flag; batch embeddings |
|Chroma disk corruption| Daily cron backup; WAL‑style persistence |
|Spec validation failures| Return 400 with validator errors; include sample CLI fixer |

---
### 13. Reference Commands
```bash
# Upload a spec
auth="Authorization: Bearer $(jwt)"
http POST :8000/v1/schemas file@petstore.yaml $auth

# Search
http POST :8000/v1/search q="create order" top_k:=5 $auth
```

---
### 14. Next Steps for the AI Engineer
1. Clone repo + run `make dev`.
2. Review `services/parser.py` TODO markers – implement `$ref` resolver.
3. Implement `vector_store.py` interface for Chroma & FAISS.
4. PR with working ingestion pipeline + search route.
5. Write at least **20 unit tests** covering edge cases.

---
**Happy hacking!** Feel free to ping the PRD author for clarifications.

