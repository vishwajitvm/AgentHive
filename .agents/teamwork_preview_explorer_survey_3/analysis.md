# Comprehensive Infrastructure, Test Suite, Documentation & Diagram Survey Report

**Agent:** `teamwork_preview_explorer_survey_3`  
**Date/Timestamp:** 2026-08-08T23:15:00Z  
**Target Repository:** `c:\python\AgentHive`  
**Working Directory:** `c:\python\AgentHive\.agents\teamwork_preview_explorer_survey_3`  

---

## Executive Summary

AgentHive is a Docker-first, multi-agent platform designed to orchestrate autonomous AI agents using a modular FastAPI backend, Next.js frontend, PostgreSQL (with pgvector), Redis, Celery, MinIO, Ollama, and a full observability stack (Prometheus, Loki, Grafana, OpenTelemetry).

This survey report provides an in-depth analysis of four core domains across the AgentHive codebase:
1. **Existing Docker & Infrastructure Setup**: Docker Compose configurations (`docker-compose.yml`, `docker-compose.dev.yml`, `docker-compose.prod.yml`), Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`), python requirements, environment configurations (`.env`, `.env.example`), and shell scripts (`scripts/start-dev.sh`, `scripts/start-prod.sh`, `kc_init.sh`).
2. **Existing Test Suite & Execution Infrastructure**: Current state of unit, integration, and end-to-end testing, test runners, API verification scripts (`test_tools.py`), missing test dependencies (`pytest`), and verification workflows (`VERIFICATION_COMMANDS.md`).
3. **Existing Documentation & System Architecture**: Analysis of root guides (`README.md`, `AI_BUILD_GUIDE.md`, `VERIFICATION_COMMANDS.md`, `CHANGELOG.md`) and `docs/` hierarchy (`ARCHITECTURE.md`, `SYSTEM_ARCHITECTURE_AND_TESTING_GUIDE.md`, `FEATURE_SPECIFICATION.md`, `DATABASE_DESIGN.md`, `docs/agents/`, `docs/tools/`).
4. **Diagram & Documentation Update Requirements**: Blueprint for updating Markdown docs and generating a valid XML `.drawio` diagram (`docs/architecture.drawio` / `docs/diagrams/architecture.drawio`) detailing smart multi-LLM fallback routing, tool orchestration, and multi-agent interaction flow.

---

## 1. Existing Docker & Infrastructure Setup

### 1.1 Docker Compose Services Architecture

The repository contains three Docker Compose files that define a 12-service architecture:

| Service Name | Container Name | Image / Build Context | Ports | Primary Function & Dependencies |
|---|---|---|---|---|
| `postgres` | `agenthive-postgres` | `pgvector/pgvector:pg16` | `5432:5432` | Relational storage & vector embeddings. Has healthcheck (`pg_isready`). |
| `redis` | `agenthive-redis` | `redis:7-alpine` | `6379:6379` | Celery message broker, caching, rate limiting. Has healthcheck (`ping`). |
| `minio` | `agenthive-minio` | `minio/minio:latest` | `9000:9000`, `9001:9001` | S3-compatible object storage for uploaded files and agent artifacts. |
| `ollama` | `agenthive-ollama` | `ollama/ollama:latest` | `11434:11434` | Local LLM inference engine (e.g. `llama3` / `llama3.1`). |
| `loki` | `agenthive-loki` | `grafana/loki:2.9.8` | `3100:3100` | Log aggregation server for container & application logs. |
| `prometheus` | `agenthive-prometheus` | `prom/prometheus:latest` | `9090:9090` | Metrics collection engine. Mounts `./infra/prometheus/prometheus.yml`. |
| `grafana` | `agenthive-grafana` | `grafana/grafana:latest` | `3001:3000` | Visual monitoring dashboard. Depends on `prometheus` & `loki`. |
| `promtail` | `agenthive-promtail` | `grafana/promtail:2.9.8` | - | Container log tailer. Ships Docker container logs to Loki. |
| `keycloak` | `agenthive-keycloak` | `quay.io/keycloak/keycloak:latest` | `8080:8080` | OIDC / OAuth2 identity provider. Depends on `postgres`. |
| `frontend` | `agenthive-frontend` | `./frontend` (`dev`/`prod`) | `3000:3000` | Next.js App Router UI dashboard. |
| `backend` | `agenthive-backend` | `./backend` (`dev`/`prod`) | `8000:8000` | FastAPI REST API engine. Depends on `postgres`, `redis`, `ollama`. |
| `worker` | `agenthive-worker` | `./backend` (`dev`/`prod`) | - | Celery background task worker with `watchdog` auto-restart in dev. |
| `scheduler` | `agenthive-scheduler` | `./backend` (`dev`/`prod`) | - | Celery beat scheduler for periodic background jobs. |
| `nginx` | `agenthive-nginx` | `nginx:alpine` (prod only) | `80:80` | Production reverse proxy routing frontend (`/`) and API (`/api`). |

### 1.2 Dockerfile Inspection

1. **`backend/Dockerfile`**:
   - Multi-stage build (`base`, `dev`, `prod`).
   - Base image: `python:3.11-slim`.
   - Packages installed: `build-essential`, `curl`.
   - Dev entrypoint: `uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`.
   - Prod entrypoint: `gunicorn app.main:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4`.

2. **`frontend/Dockerfile`**:
   - Multi-stage build (`base`, `dev`, `deps`, `build`, `prod`).
   - Base image: `node:20-alpine`.
   - Dev entrypoint: `npm run dev`.
   - Prod entrypoint: `npm start` with optimized standalone output from `.next`.

### 1.3 Python Dependencies (`backend/requirements.txt`)

Current dependencies in `backend/requirements.txt`:
```text
fastapi, uvicorn[standard], gunicorn, pydantic-settings, sqlalchemy, psycopg[binary],
redis, celery, watchdog, structlog, loguru, opentelemetry-api, opentelemetry-sdk,
httpx, python-multipart, cryptography, pgvector, youtube-transcript-api,
prometheus-fastapi-instrumentator, email-validator, tracenest==0.1.15, asyncpg,
beautifulsoup4, pymupdf, pandas, passlib[bcrypt], bcrypt, PyJWT, pyotp
```
*Gap Identified for Tool & Agent Expansion (R2)*: `pytest` and `pytest-asyncio` are missing. For expanded tool categories (web search, document writing, text processing, data utilities, developer tools), additional libraries such as `python-docx`, `openpyxl`, `tabulate`, `sympy`, `pillow`, `matplotlib`, `duckduckgo-search`, `pypdf`/`pdfplumber` should be added to `backend/requirements.txt`.

### 1.4 Environment Configuration (`.env` vs `.env.example`)

- Both files specify variables for Database (`POSTGRES_*`), Redis (`REDIS_*`), MinIO (`MINIO_*`), Ollama (`OLLAMA_*`), LLM Provider Keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `HUGGINGFACE_API_KEY`, `GROQ_API_KEY`), Default Model Policy (`DEFAULT_PRIMARY_PROVIDER=gemini`, `DEFAULT_SECONDARY_PROVIDER=ollama`, `DEFAULT_FALLBACK_ORDER=gemini,ollama,huggingface,groq,openai`), Logging (`LOG_LEVEL`, `ENABLE_OTEL`, `LOKI_URL`), and Security (`SECRET_KEY`, `ENCRYPTION_KEY`).
- `.env` contains local development values and keys (e.g. Gemini key `AQ.Ab8RN6I...`, Groq key `gsk_FSrxg...`, HuggingFace key `hf_VDMz...`). `.env.example` provides clean template defaults for new setups.

### 1.5 Helper Scripts (`scripts/`)

- `scripts/start-dev.sh`: Executes `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build`.
- `scripts/start-prod.sh`: Executes `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`.

---

## 2. Existing Test Suite & Execution Infrastructure

### 2.1 Current State of Automated Testing

1. **`backend/tests` Directory**:
   - Currently **empty** (0 files). No pytest test files (`test_*.py`) exist in `backend/tests/` or subdirectories.
2. **`test_tools.py` Script (Root)**:
   - An ad-hoc verification script using Python's standard `urllib.request`.
   - Tests HTTP GET on `http://localhost:8000/` and `/ready`.
   - Tests HTTP POST calls to:
     - `/api/tools/code_tool/run` (expression: `2 + 2`)
     - `/api/tools/file_tool/run` (action: write/read `test.txt`)
     - `/api/tools/search_tool/run` (query: `fastapi`)
     - `/api/tools/youtube_transcript_tool/run` (url: YouTube sample)
3. **`VERIFICATION_COMMANDS.md`**:
   - Documents manual testing procedures:
     - Container health check: `docker compose ps`
     - Health API check: `curl http://localhost:8000/ready`
     - Agent listing: `Invoke-RestMethod -Uri http://localhost:8000/api/agents`
     - Sync Agent Execution: `curl -X POST http://localhost:8000/api/agents/1/run -d '{"query": "hello"}'`
     - Log inspection: `docker logs --tail 150 agenthive-backend`
     - Ollama model pull: `docker exec agenthive-ollama ollama pull llama3`

### 2.2 Test Suite Architecture Gaps & Requirements

To achieve a production-grade multi-agent engine:
1. **Test Framework Installation**: Add `pytest`, `pytest-asyncio`, `pytest-cov`, and `httpx` to `backend/requirements.txt`.
2. **Directory Structure in `backend/tests/`**:
   ```text
   backend/tests/
   ├── conftest.py                   # Pytest fixtures (async db session, mock LLM router, client)
   ├── unit/
   │   ├── test_llm_router.py        # Test model policy engine, fallback order, key resolution
   │   ├── test_agent_orchestrator.py# Test agent selection, prompt versioning, memory injection
   │   ├── test_tools_registry.py    # Test individual tool execution, parameter parsing, allowlists
   │   └── test_security.py          # Test secret encryption/decryption, JWT auth
   ├── integration/
   │   ├── test_api_health.py        # Test /health and /ready routes
   │   ├── test_api_agents.py        # Test agent CRUD and execution endpoints
   │   ├── test_api_tools.py         # Test tool execution REST endpoints
   │   └── test_workflows.py         # Test DAG execution and retry logic
   ```
3. **Execution Commands**:
   - Unit tests: `pytest backend/tests/unit`
   - Integration tests: `pytest backend/tests/integration`
   - Docker container test execution: `docker exec agenthive-backend pytest backend/tests/`

---

## 3. Existing Documentation & Knowledge Base

### 3.1 Root Documentation Files

1. **`README.md`**: Overview of AgentHive, project goals (free-first, Docker-first, multi-LLM router with Gemini primary / Ollama fallback, TOON prompt format), detailed tech stack matrix, high-level data flow, repository structure, and local/prod run instructions.
2. **`AI_BUILD_GUIDE.md`**: 18 absolute build rules for AI coding assistants, 9 implementation phases (Phase 0 to Phase 8), documentation update matrix, coding standards (FastAPI, Pydantic, SQLAlchemy, Next.js), and explicit "Do Not Do" anti-patterns.
3. **`VERIFICATION_COMMANDS.md`**: Executable verification command reference and doc update process rules.
4. **`CHANGELOG.md`**: Release history (`[0.1.0-MVP]`, `[0.2.0-MVP]`).

### 3.2 `docs/` Directory Hierarchy

- **`docs/ARCHITECTURE.md`**: Explains the modular monolith architecture style (`backend/app/{api, agents, llm, tools, workflows, memory, jobs, logging}`), Mermaid sequence/flow diagrams, request handling flow, agent runtime rules (`Agent -> LLMRouter -> ProviderAdapter -> Model`), LLM fallback triggers, data persistence rules, and horizontal scaling plan.
- **`docs/SYSTEM_ARCHITECTURE_AND_TESTING_GUIDE.md`**: 2762-line master guide containing detailed service maps, end-to-end data flows, credentials, debugging checklists, and developer verification procedures.
- **`docs/FEATURE_SPECIFICATION.md`**: Component specifications for LLM router, agent runtime, tool registry, workflow engine, memory, auth, and observability.
- **`docs/DATABASE_DESIGN.md`**: Database schema specs for `agents`, `agent_versions`, `prompts`, `prompt_versions`, `model_providers`, `model_policies`, `agent_runs`, `llm_calls`, `tool_calls`, `secrets`.
- **`docs/agents/`**: 26 detailed markdown specifications for individual agents (e.g. `end_truth_agent.md`, `data_analyst.md`, `bug_triage.md`).
- **`docs/tools/`**: 26 detailed markdown specifications for individual tools (e.g. `code_tool.md`, `pdf_tool.md`, `search_tool.md`, `youtube_transcript_tool.md`).
- **`docs/diagrams/`**: 10 `.drawio` XML files (`llm-router-fallback.drawio`, `backend-flow.drawio`, `full-system-architecture.drawio`, etc.).

---

## 4. Requirements for Documentation & Architecture `.drawio` Diagram

### 4.1 Requirements for Updated Markdown Documentation (`docs/`)

The multi-agent orchestration upgrade (R1 & R2) requires updating/creating markdown documentation covering:
1. **Multi-Agent Orchestration Architecture (`docs/ARCHITECTURE.md`)**:
   - Explanation of task routing strategies (Hierarchical Router, Swarm Orchestrator, Specialist Agent Selector).
   - Agent interaction flow: User Query -> Task Router -> Agent Selection -> Memory Retrieval (pgvector/TOON) -> Tool Execution -> Multi-LLM Call (Router) -> Response Synthesis.
   - Smart Multi-LLM Fallback & Policy Engine: Primary provider selection, fallback sequence (`Gemini` -> `Ollama` -> `HuggingFace` -> `Groq` -> `OpenAI`), failover triggers (quota, rate limit, context window overflow, provider timeout, invalid output format).
   - Tool Orchestration Engine: Dynamic tool discovery, permission allowlists per agent, input schema validation, sandboxed execution, response truncation/formatting.
2. **Expanded Tool & Agent Specifications (`docs/FEATURE_SPECIFICATION.md`, `docs/tools/`, `docs/agents/`)**:
   - Documentation for all new web, document, text, utility, and developer tools.
   - Documentation for newly registered specialized agents and routing policies.

### 4.2 Requirements for `.drawio` Architecture Diagram (`docs/architecture.drawio` / `docs/diagrams/architecture.drawio`)

The `.drawio` diagram must be a syntactically valid XML document using standard Draw.io schema elements (`<mxfile>`, `<diagram>`, `<mxGraphModel>`, `<root>`, `<mxCell>`).

#### Required Visual Components in `.drawio`:
1. **Client & Ingress Layer**:
   - User UI (Next.js Dashboard `:3000`)
   - Nginx Reverse Proxy / Keycloak Authentication (`:8080`)
2. **Orchestration & Task Router Layer**:
   - FastAPI Ingress API (`:8000`)
   - Multi-Agent Orchestrator / Router Node
   - Agent Registry & Selector
3. **Specialized Agent Pool**:
   - General Assistant Agent
   - Web Search Agent
   - Document & Data Analyst Agent
   - Developer / Code Execution Agent
   - Fact Checker / Truth Verification Agent
4. **Tool Orchestration Layer**:
   - Tool Registry & Allowlist Validator
   - Tool Subsystems: Web Tools (Search, Scraper, YouTube), Document Tools (PDF, CSV, Docx), Text Tools (Summarizer, Translator), Developer Tools (Python Interpreter, File System, Code Runner), Utility Tools (Postgres, Redis, MinIO, Loki).
5. **Memory & Context Optimization Layer**:
   - Vector Store (pgvector)
   - Context Formatter (TOON / compact key-value memory context)
6. **Smart Multi-LLM Routing & Fallback Engine**:
   - Model Policy Engine
   - Provider Adapters & Fallback Cascade:
     - Primary: Gemini Cloud API
     - Fallback 1: Ollama Local (`llama3`)
     - Fallback 2: Hugging Face API
     - Fallback 3: Groq API
     - Fallback 4: OpenAI API
7. **Data Persistence & Observability Stack**:
   - PostgreSQL (Relational Agent/Run State)
   - Redis (Celery Broker & Cache)
   - MinIO (Object Storage)
   - Observability Pipeline (OpenTelemetry -> Prometheus & Loki -> Grafana `:3001`)

---

## 5. Summary Table of Actionable Recommendations

| Area | Component | Current State | Recommendation for Implementation Team |
|---|---|---|---|
| Infrastructure | Docker Setup | 12 containers configured in Compose; dev & prod targets operational. | Ensure any new system tools (e.g. system binaries for OCR/PDF) are included in `backend/Dockerfile`. Update `docker-compose.yml` if new services are needed. |
| Testing | Test Suite | `backend/tests` is empty; `test_tools.py` in root is manual script. | Add `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` to `backend/requirements.txt`. Build `unit/` and `integration/` test suites in `backend/tests/`. |
| Dependencies | `requirements.txt` | Core packages present; missing pytest and tool expansion libraries. | Append `pytest`, `pytest-asyncio`, `python-docx`, `openpyxl`, `sympy`, `tabulate`, `pillow` to `backend/requirements.txt`. |
| Documentation | Markdown Docs | Rich baseline docs exist; needs update for multi-agent router & expanded tool catalog. | Update `docs/ARCHITECTURE.md`, `docs/FEATURE_SPECIFICATION.md`, and `CHANGELOG.md` with multi-agent orchestration details. |
| Diagrams | `.drawio` File | 10 existing diagrams in `docs/diagrams/`; main overall architecture diagram needed. | Create `docs/architecture.drawio` (and sync to `docs/diagrams/full-system-architecture.drawio`) with valid XML formatting covering routing, tools, agents, fallback LLMs, and observability. |

---

*Report compiled by agent `teamwork_preview_explorer_survey_3`.*
