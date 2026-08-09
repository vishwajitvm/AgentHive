# Change Log — Milestone 4 (M4)

## Summary of Changes
Implemented Milestone 4 (Dependencies, Environment Configs & Docker Integration) for AgentHive.

### 1. `backend/requirements.txt`
- Added missing test suite dependencies: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Verified all core, database, tool, and observability dependencies required for the 40 registered tools, `MultiAgentEngine`, and automated testing suite:
  - `fastapi`, `uvicorn[standard]`, `gunicorn`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `redis`, `celery`, `watchdog`, `structlog`, `loguru`, `opentelemetry-api`, `opentelemetry-sdk`, `httpx`, `python-multipart`, `cryptography`, `pgvector`, `youtube-transcript-api`, `prometheus-fastapi-instrumentator`, `email-validator`, `tracenest==0.1.15`, `asyncpg`, `beautifulsoup4`, `pymupdf`, `pandas`, `passlib[bcrypt]`, `bcrypt`, `PyJWT`, `pyotp`, `python-docx`, `openpyxl`, `python-pptx`, `pytesseract`, `pyyaml`, `feedparser`, `dnspython`, `python-whois`, `markdown`, `sympy`, `Pillow`, `gitpython`, `sqlparse`, `jsonschema`, `wikipedia-api`, `nltk`, `sumy`, `pytest`, `pytest-asyncio`, `pytest-cov`.

### 2. `.env.example`
- Updated with comprehensive documentation across 12 configuration categories.
- Added Multi-Agent Engine & Speculative LLM Racing settings (`DEFAULT_ORCHESTRATION_PATTERN`, `PARALLEL_LLM_RACING_ENABLED`, `PARALLEL_LLM_TIMEOUT_SECONDS`, `PARALLEL_LLM_DEFAULT_PROVIDERS`).
- Documented LLM Provider API Keys (`GEMINI_API_KEY`, `OPENAI_API_KEY`, `HUGGINGFACE_API_KEY`, `GROQ_API_KEY`, custom endpoints) and Fallback Order Policy.
- Documented Tool Execution & Sandbox Flags (`ENABLE_TOOL_SANDBOX`, `TOOL_TIMEOUT_SECONDS`, `DISABLE_UNSAFE_TOOLS`, `MAX_TOOL_RESULT_LENGTH`).
- Documented Database, Redis, MinIO, OpenTelemetry & Loki configuration variables.

### 3. `backend/Dockerfile`
- Updated `base` image target apt-get installation to include system-level dependencies for document/OCR tools:
  - `build-essential`, `curl`, `git`, `tesseract-ocr`, `poppler-utils`, `libmagic1`.

### 4. Docker Compose Configurations Verification
- Verified YAML syntax and service structure for:
  - `docker-compose.yml` (PostgreSQL pgvector, Redis, MinIO, Ollama, Loki, Prometheus, Grafana, Promtail, Keycloak)
  - `docker-compose.dev.yml` (frontend, backend, worker, scheduler dev containers)
  - `docker-compose.prod.yml` (frontend, backend, worker, scheduler, nginx production containers)
