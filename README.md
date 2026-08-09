# AgentHive — Advanced Multi-Agent Orchestration Architecture

AgentHive is a free-first, Docker-first multi-agent orchestration platform for deploying, managing, observing, and executing specialized AI agents from a unified dashboard.

Designed for scalable multi-agent teamwork, AgentHive features dynamic pattern orchestration (Supervisor, Swarm, Router), speculative parallel LLM racing, a modular 40-tool catalog, and full observability integrations.

---

## Key Features

1. **Multi-Agent Orchestration Engine (`MultiAgentEngine`)**:
   - **Supervisor Pattern**: Decomposes complex user requests into discrete sub-tasks, delegates sub-tasks to specialized sub-agents, and synthesizes findings into a unified final answer.
   - **Swarm Pattern**: Enables dynamic peer-to-peer control transfers using `[HANDOFF] agent_slug | {context}` tags with execution loop safeguards (`max_handoffs`).
   - **Router Pattern**: Conducts fast intent classification to route queries directly to the optimal specialized agent.
   - **Auto Mode**: Classifies intent and automatically selects the optimal orchestration pattern.

2. **Speculative Parallel Multi-LLM Racing (`LLMRouter.generate_parallel()`)**:
   - Queries multiple configured providers concurrently (Gemini 1.5 Flash, Groq Llama3, Ollama Local, OpenAI GPT-4o-mini, HuggingFace Llama 3.2).
   - Utilizes `asyncio.wait(..., return_when=FIRST_COMPLETED)` to return the fastest response instantly and cancel pending calls.

3. **Categorized 40-Tool Catalog (`backend/app/tools/modules/`)**:
   - **13 Infrastructure Base Tools**: `file_tool`, `postgres_tool`, `redis_tool`, `minio_tool`, `loki_tool`, `code_tool`, `scraper_tool`, `translation_tool`, `youtube_transcript_tool`, `md_writer_tool`, `search_tool`, `pdf_tool`, `csv_reader_tool`.
   - **9 Web Tools**: `wikipedia_tool`, `arxiv_tool`, `rss_reader_tool`, `url_checker_tool`, `weather_tool`, `dns_lookup_tool`, `whois_tool`, `hacker_news_tool`, `github_repo_tool`.
   - **5 Document Tools**: `docx_tool`, `excel_writer_tool`, `pptx_tool`, `ocr_tool`, `json_yaml_tool`.
   - **5 Text & NLP Tools**: `sentiment_tool`, `text_summarizer_tool`, `diff_tool`, `keyword_extractor_tool`, `markdown_to_html_tool`.
   - **5 Utility Tools**: `calculator_tool`, `datetime_tool`, `image_metadata_tool`, `hash_crypto_tool`, `zip_archiver_tool`.
   - **3 Developer Tools**: `git_tool`, `sql_query_builder_tool`, `json_schema_validator`.

4. **REST API Endpoint Extensions**:
   - `POST /api/orchestrate`: Dynamic multi-agent pattern execution endpoint.
   - `POST /api/agents/{id}/run`: Direct or delegated multi-agent run endpoint.

5. **Full Observability & Traceability Stack**:
   - Grafana Loki (:3100) container log aggregation.
   - Prometheus (:9090) endpoint and LLM latency scraping.
   - OpenTelemetry distributed tracing spans.
   - Grafana (:3001) visual dashboards.

---

## Recommended Technology Stack

| Component | Technology | Role |
|---|---|---|
| Frontend | Next.js + React + Tailwind CSS | Interactive dashboard & monitoring UI |
| Backend API | Python FastAPI | REST API & multi-agent orchestration |
| Multi-Agent Engine | Custom `MultiAgentEngine` | Supervisor, Swarm, and Router pattern execution |
| LLM Router | Custom `LLMRouter` | Speculative parallel racing & provider fallbacks |
| Database & Vector | PostgreSQL + pgvector | Persistent data, execution logs, & embeddings |
| Queue & Cache | Redis + Celery | Async agent tasks & job queues |
| Storage | MinIO | S3-compatible workspace document storage |
| Local LLM | Ollama | Zero-cost local inference fallback |
| Observability | Loki + Prometheus + OpenTelemetry + Grafana | Logs, metrics, tracing, & dashboards |

---

## Architecture & Verification

### Architecture Diagram
The XML architecture diagram is available in:
- `docs/architecture.drawio`
- `docs/diagrams/multi-agent-architecture.drawio`

### Diagram XML Schema Verification
Run the verification script to confirm valid XML schema structure and architectural keywords:
```bash
python docs/verify_drawio.py
```

### Pytest Verification Suite
Run unit and integration tests across multi-agent engine, speculative LLM router, and tool catalog:
```bash
pytest backend/tests/ -v
```

---

## Running Locally

1. Start all containerized services:
```bash
docker compose up -d --build
```

2. Access core services:
- **Frontend Dashboard**: `http://localhost:3000`
- **FastAPI OpenAPI Documentation**: `http://localhost:8000/docs`
- **Grafana Monitoring**: `http://localhost:3001` (admin / admin)
- **MinIO Storage Console**: `http://localhost:9001` (agenthive / agenthive123)
