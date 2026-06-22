# AgentHive Implementation Plan

AgentHive is a Docker-first, free-first, scalable multi-agent platform designed to create, configure, deploy, monitor, and control multiple AI agents from a central dashboard. This plan details the step-by-step chronological implementation of the entire AgentHive MVP stack.

## User Review Required

> [!IMPORTANT]
> - **Encryption Key**: We will add a symmetric Fernet encryption key (`SECRET_ENCRYPTION_KEY`) in the `.env` file to encrypt provider API keys in the database.
> - **Direct HTTP Provider Integrations**: To avoid heavy and potentially conflicting third-party SDK dependencies (Google, OpenAI, Groq, Hugging Face, etc.), the LLM Router and its provider adapters will use asynchronous HTTP requests using `httpx.AsyncClient` to directly communicate with provider REST endpoints. This is highly performant, fully async, and makes timeouts, fallbacks, and error parsing uniform.
> - **No Auth for MVP**: In line with the "free-first, local-first developer workspace" goal, the dashboard will run session-free without a login page, granting full dashboard controls directly to the developer.

## Open Questions

> [!NOTE]
> 1. **Default Local Model**: For the Ollama local fallback, should we pre-select a default model (e.g. `llama3` or `phi3` or `mistral`) that the router will request if Gemini fails, and would you like a dashboard button to trigger Ollama pulling that model?
> 2. **Mock Web Searches**: For the Research Agent's Search Tool, when Google/Serper API keys are not supplied in Settings, should we implement a mock search service that returns relevant Wikipedia-style extracts and logs it as a mock tool call, preventing agent failures during local testing?

---

## Proposed Changes

### Docker & Infrastructure

Improve Docker configs to ensure complete monitoring, logging, and reverse proxy setup.

#### [MODIFY] [docker-compose.yml](file:///c:/python/AgentHive/docker-compose.yml)
- Configure `promtail` service to collect application and system container logs, forwarding them to `loki`.
- Define network boundaries and ensure all data volumes are named and persistent.

#### [NEW] [promtail-config.yml](file:///c:/python/AgentHive/infra/promtail/promtail-config.yml)
- Configure Promtail shipping parameters: scrape jobs for Docker containers, scraping `/var/lib/docker/containers/*/*.log` or writing to shared logs directory, shipping to Loki URL `http://loki:3100/loki/api/v1/push`.

#### [MODIFY] [docker-compose.dev.yml](file:///c:/python/AgentHive/docker-compose.dev.yml)
- Connect all services. Set backend auto-reload, frontend watchpack polling, Celery worker watchdog, and database volume mapping.

#### [MODIFY] [docker-compose.prod.yml](file:///c:/python/AgentHive/docker-compose.prod.yml)
- Set up optimized builds. Ensure restart policies (`unless-stopped`), Nginx reverse proxy mounting, and production-level logging.

---

### Backend Core

Set up the database, encryption utility, exception definitions, and TOON token optimization utilities.

#### [MODIFY] [requirements.txt](file:///c:/python/AgentHive/backend/requirements.txt)
- Add: `cryptography` (for encrypting keys), `pgvector` (for database vector operations).

#### [MODIFY] [config.py](file:///c:/python/AgentHive/backend/app/core/config.py)
- Add settings for `secret_encryption_key`, MinIO credentials, S3 buckets, and default fallback parameters.

#### [NEW] [database.py](file:///c:/python/AgentHive/backend/app/core/database.py)
- Initialize SQLAlchemy async engine, async session maker, and Base metadata.
- Implement `init_db()` to run database migrations, execute `CREATE EXTENSION IF NOT EXISTS vector;`, and create all tables.

#### [NEW] [security.py](file:///c:/python/AgentHive/backend/app/core/security.py)
- Implement Fernet-based symmetric encryption helpers: `encrypt_secret(key: str) -> str` and `decrypt_secret(encrypted: str) -> str` to encrypt third-party provider API keys.

#### [NEW] [exceptions.py](file:///c:/python/AgentHive/backend/app/core/exceptions.py)
- Define custom application exceptions: `LLMRouteError`, `AgentRunError`, `WorkflowValidationError`, `ToolExecutionError`. Include global exception handlers for FastAPI.

#### [NEW] [toon.py](file:///c:/python/AgentHive/backend/app/core/toon.py)
- Implement TOON optimization utilities:
  - `compress_prompt(text: str) -> str` (whitespace reduction, instruction outlining).
  - `summarize_tool_result(result: str, max_chars: int = 1000) -> str` (keep core info, archive full text).
  - `format_memory_context(memories: list) -> str` (custom compact list format).
  - `format_agent_context(system_prompt: str, history: list) -> str` (compact key-value template format for sending to LLM).

---

### Database Models

Create structured database tables using SQLAlchemy async models.

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/core/models.py)
- Models for `User` (email, name, role, status), `Secret` (name, encrypted_value), and `AuditLog` (action_type, description, metadata).

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/agents/models.py)
- Models for `Agent` (name, slug, system_prompt, tools_enabled, memory_enabled, max_steps, timeout_seconds), `AgentVersion` (snapshot of agent), and `Prompt` / `PromptVersion`.

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/llm/models.py)
- Models for `ModelProvider` (provider_name, provider_type, base_url, api_key_secret_id, default_model, enabled, health_status) and `ModelPolicy` (primary_provider, secondary_provider, fallback_order, timeouts, retries).

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/workflows/models.py)
- Models for `Workflow` (name, definition_json, status), `WorkflowRun` (status, input, output, error), and `WorkflowStep` (node_id, status, input, output).

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/logs/models.py)
- Models for `AgentRun` (agent_id, status, input, output), `AgentStep` (action_type, content, metadata), `LLMCall` (provider, model, prompt_tokens, latency, status, fallback_reason), and `ToolCall` (tool_name, tool_input, tool_output, latency).

---

### LLM Providers & Router

Implement the LLM provider interfaces and routing engine with fallback policies.

#### [NEW] [base.py](file:///c:/python/AgentHive/backend/app/llm/providers/base.py)
- Abstract base provider class defining interface `async def generate(self, prompt: str, system_instruction: str, max_tokens: int, timeout: float) -> str`.

#### [NEW] [gemini.py](file:///c:/python/AgentHive/backend/app/llm/providers/gemini.py)
- Gemini REST adapter calling Google GenAI API endpoint.

#### [NEW] [ollama.py](file:///c:/python/AgentHive/backend/app/llm/providers/ollama.py)
- Ollama REST adapter calling local Ollama `/api/chat` or `/api/generate` endpoint.

#### [NEW] [openai.py](file:///c:/python/AgentHive/backend/app/llm/providers/openai.py)
- OpenAI REST adapter calling `/v1/chat/completions`.

#### [NEW] [huggingface.py](file:///c:/python/AgentHive/backend/app/llm/providers/huggingface.py)
- Hugging Face API inference adapter.

#### [NEW] [groq.py](file:///c:/python/AgentHive/backend/app/llm/providers/groq.py)
- Groq REST adapter.

#### [NEW] [policy.py](file:///c:/python/AgentHive/backend/app/llm/policy.py)
- Helper class to resolve provider overrides and configuration flags.

#### [MODIFY] [router.py](file:///c:/python/AgentHive/backend/app/llm/router.py)
- Core routing logic: fetch current active policy, loop through healthy fallback chain providers, invoke adapter, log outputs/tokens/latency, and handle exceptions to execute fallbacks.

---

### Tools & Agent Orchestrator

Build the core agent loop and default tool systems.

#### [NEW] [base.py](file:///c:/python/AgentHive/backend/app/tools/base.py)
- Base abstract tool class.

#### [NEW] [registry.py](file:///c:/python/AgentHive/backend/app/tools/registry.py)
- Registries and implementation classes for:
  - `FileTool`: read/write local workspace files.
  - `PDFTool`: parse text from PDFs.
  - `SearchTool`: query web results (with mock fallback).
  - `StorageTool`: save/fetch objects from MinIO.
  - `CodeTool`: evaluate simple python mathematical code.

#### [MODIFY] [base.py](file:///c:/python/AgentHive/backend/app/agents/base.py)
- Core agent execution loop. Resolves prompts, invokes `LLMRouter`, validates tool allowlist, executes tools, logs steps, handles loop limit, and structures final output.

#### [NEW] [registry.py](file:///c:/python/AgentHive/backend/app/agents/registry.py)
- Registry of default agents (Personal Assistant, Task, PDF/Document, Research, Developer).

#### [NEW] [orchestrator.py](file:///c:/python/AgentHive/backend/app/agents/orchestrator.py)
- Core service to trigger agent runs synchronously or schedule them via Celery background tasks.

---

### Workflow Engine, Memory, and Logs

Implement workflow execution, vector memory, and logs retrieving.

#### [NEW] [engine.py](file:///c:/python/AgentHive/backend/app/workflows/engine.py)
- Directed Acyclic Graph (DAG) validator. Workflow executor traversing workflow steps, scheduling jobs, evaluating conditions, handling retries, and recording results.

#### [NEW] [embeddings.py](file:///c:/python/AgentHive/backend/app/memory/embeddings.py)
- Compute text embeddings using Gemini or local Ollama.

#### [NEW] [vector_store.py](file:///c:/python/AgentHive/backend/app/memory/vector_store.py)
- Store and query memories semantically using Postgres pgvector.

#### [NEW] [service.py](file:///c:/python/AgentHive/backend/app/logs/service.py)
- Service to query and filter execution steps, tool calls, and LLM router fallbacks.

---

### API Routes & Middleware

Add routes for the frontend dashboard and register services on start.

#### [MODIFY] [main.py](file:///c:/python/AgentHive/backend/app/main.py)
- Create database tables and initialize default providers on startup. Add request tracking middlewares.

#### [MODIFY] [health.py](file:///c:/python/AgentHive/backend/app/api/health.py)
- Complete `/health` and `/ready` checks, pinging PostgreSQL, Redis, MinIO, and Ollama.

#### [NEW] [agents.py](file:///c:/python/AgentHive/backend/app/api/routes/agents.py)
- CRUD endpoints for agents, prompts, and runs.

#### [NEW] [models.py](file:///c:/python/AgentHive/backend/app/api/routes/models.py)
- CRUD endpoints for model providers and policies.

#### [NEW] [workflows.py](file:///c:/python/AgentHive/backend/app/api/routes/workflows.py)
- CRUD endpoints for workflows and workflow runs.

#### [NEW] [logs.py](file:///c:/python/AgentHive/backend/app/api/routes/logs.py)
- Endpoints to fetch logs, step activities, fallback counts, and token counts.

#### [NEW] [settings.py](file:///c:/python/AgentHive/backend/app/api/routes/settings.py)
- Manage secret API keys, Ollama URLs, and system settings.

#### [MODIFY] [worker.py](file:///c:/python/AgentHive/backend/app/jobs/worker.py)
- Implement Celery jobs `execute_agent_run` and `execute_workflow_run`.

---

### Frontend Dashboard

Create Tailwind styles, layout shell, page views, and API client methods.

#### [NEW] [tailwind.config.js](file:///c:/python/AgentHive/frontend/tailwind.config.js)
- Standard Tailwind CSS content and theme config.

#### [NEW] [postcss.config.js](file:///c:/python/AgentHive/frontend/postcss.config.js)
- PostCSS standard configuration.

#### [NEW] [globals.css](file:///c:/python/AgentHive/frontend/src/app/globals.css)
- Import Tailwind layers and define custom CSS scrollbars and layout tokens.

#### [NEW] [layout.tsx](file:///c:/python/AgentHive/frontend/src/app/layout.tsx)
- Unified dashboard shell featuring a premium sidebar, topbar showing connection status, and notifications.

#### [MODIFY] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/page.tsx)
- Home dashboard page displaying card stats, provider health grids, token usage charts, and live fallback activity tables.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/page.tsx)
- List and status of all created agents, with actions to delete, modify, or launch.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/create/page.tsx)
- Complex agent builder screen setting prompt details, model overrides, and permitted tools.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/[id]/page.tsx)
- Agent detail panel with an interactive chat window, displaying steps, tool inputs, and LLM logs in a side drawer.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/models/page.tsx)
- Provider status grid and active fallback policy builder.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/tools/page.tsx)
- Tool listing showing configuration, code examples, and activity counts.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/workflows/page.tsx)
- Visual listing and creation form for multi-agent DAG workflows.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/logs/page.tsx)
- Global log browser with full filters (Request ID, Agent, LLM, Tool) and pagination.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/env/page.tsx)
- Settings panel to configure credential API keys (Gemini, Groq, Hugging Face, etc.) safely masked.

#### [NEW] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/monitoring/page.tsx)
- Web console references linking to Grafana / Prometheus configurations.

#### [MODIFY] [api.ts](file:///c:/python/AgentHive/frontend/src/lib/api.ts)
- Comprehensive API client methods connecting to all FastAPI endpoints.

#### [NEW] [components/](file:///c:/python/AgentHive/frontend/src/components/)
- Reusable components: Card, Table, Loading, Sidebar, Header, Modal.

---

### Documentation & Logs

#### [MODIFY] [CHANGELOG.md](file:///c:/python/AgentHive/CHANGELOG.md)
- Log implementation entries for version `0.2.0-MVP`.

#### [MODIFY] [docs/](file:///c:/python/AgentHive/docs/)
- Review and update matching docs to align with code changes (specifically `DATABASE_DESIGN.md`, `EDGE_CASES.md`, `TECH_STACK.md`, `DEPLOYMENT_LOCAL.md`, and `FEATURE_SPECIFICATION.md`).

---

## Verification Plan

### Automated Tests
- Create validation scripts to run API tests and verify schema validity.
- Run python tests inside the dev backend container:
  ```bash
  docker compose exec backend pytest app/tests
  ```

### Manual Verification
- Deploy the dev environment:
  ```bash
  docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
  ```
- Access `http://localhost:3000` to verify:
  1. Frontend dashboard correctly boots and loads.
  2. Health checks for PostgreSQL, Redis, Ollama, and MinIO report green status.
  3. API keys can be saved and retrieved in masked formats.
  4. Creating and running an agent successfully loops, triggers LLM Router, falls back to Ollama on simulated Gemini timeout, and records steps properly.
  5. Structured logs show `request_id` and masked values.
