# AgentHive AI Build Guide

This file is for Antigravity, Codex, Claude, or any AI coding assistant that will build AgentHive.

## Absolute Build Rules

1. Build chronologically. Do not jump to advanced agents before foundation is ready.
2. Keep frontend and backend separated.
3. Everything must run through Docker.
4. Development Docker must support hot reload.
5. Production Docker must be optimized and stable.
6. Do not hardcode LLM providers inside agents.
7. All model/provider settings must come from database/config service.
8. Gemini is the default primary model.
9. Ollama is the default fallback model.
10. Dashboard must allow changing primary, secondary, and fallback order.
11. Use JSON for APIs and database records.
12. Use TOON or compact key-value format for LLM context to reduce token usage.
13. Log every meaningful operation.
14. Never log raw secrets.
15. Every feature change must update docs and changelog.
16. Avoid hallucinated features. If implementation is not present, mark it as planned.
17. Write clean, typed, testable, modular code.
18. Keep all environment variables documented in `.env.example`.

## Implementation Phases

### Phase 0 - Repository Foundation

Create or verify:

```text
backend/
frontend/
docs/
infra/
scripts/
docker-compose.yml
docker-compose.dev.yml
docker-compose.prod.yml
.env.example
.gitignore
README.md
CHANGELOG.md
```

Acceptance criteria:

- Docker Compose starts infrastructure services.
- Frontend and backend folders exist.
- README explains setup.
- Docs exist and are version-aware.

### Phase 1 - Docker Development Environment

Implement:

- Frontend Dockerfile with dev target.
- Backend Dockerfile with dev target.
- PostgreSQL with pgvector.
- Redis.
- MinIO.
- Ollama.
- Nginx.
- Prometheus.
- Grafana.
- Loki.
- Promtail.

Acceptance criteria:

- `docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build` works.
- Frontend changes reflect immediately.
- Backend API changes reflect immediately.
- PostgreSQL data persists.
- Ollama model volume persists.

### Phase 2 - Backend Core

Implement modules:

```text
app/core/config.py
app/core/database.py
app/core/security.py
app/logging/logger.py
app/api/health.py
app/api/routes.py
app/main.py
```

Acceptance criteria:

- `/health` returns backend status.
- `/ready` checks database, Redis, and Ollama health.
- Structured logs include request_id.
- OpenAPI docs load correctly.

### Phase 3 - Dashboard Shell

Create pages:

```text
/dashboard
/agents
/models
/tools
/workflows
/logs
/settings/env
```

Acceptance criteria:

- Dashboard layout is responsive.
- Sidebar navigation works.
- API health is displayed.
- No hardcoded fake critical data unless clearly marked as mock.

### Phase 4 - LLM Router

Build provider-agnostic LLM layer:

```text
BaseLLMProvider
GeminiProvider
OllamaProvider
HuggingFaceProvider
OpenAIProvider
GroqProvider
CustomProvider
LLMRouter
ModelPolicyEngine
```

Default policy:

```text
primary=gemini
secondary=ollama
fallback_order=gemini,ollama,huggingface,groq,gpt
```

Acceptance criteria:

- Agent calls only `LLMRouter.generate()`.
- Router chooses provider based on dashboard settings.
- If Gemini fails due to quota/token/rate limit/timeout, fallback runs.
- Fallback reason is logged.

### Phase 5 - Agent Runtime

Build:

```text
BaseAgent
AgentRegistry
AgentOrchestrator
AgentRunService
AgentStepLogger
```

Acceptance criteria:

- Agent can run with selected model.
- Every step is logged.
- Max steps and timeouts are enforced.
- Infinite loops are blocked.

### Phase 6 - Tool System

Build tool abstraction:

```text
BaseTool
ToolRegistry
FileTool
PDFTool
SearchTool
CodeTool
StorageTool
```

Acceptance criteria:

- Tools can be enabled/disabled per agent.
- Tool input/output summaries are logged.
- Raw sensitive content is not logged by default.

### Phase 7 - Workflow Engine

Build:

```text
WorkflowDefinition
WorkflowNode
WorkflowExecutor
WorkflowRunLogger
RetryPolicy
DeadLetterQueue
```

Acceptance criteria:

- Workflow DAG validation prevents circular flows.
- Failed nodes can retry with limit.
- Manual resume is possible.
- Workflow runs are visible in dashboard.

### Phase 8 - Observability

Implement:

- Structlog/Loguru structured app logs.
- OpenTelemetry trace IDs.
- Loki log shipping.
- Prometheus metrics.
- Grafana dashboards.
- PostgreSQL audit tables.

Acceptance criteria:

- User can see exactly what bot is doing.
- Agent run timeline is visible.
- LLM fallback events are visible.
- Tool calls are visible.
- Errors are searchable.

## Documentation Update Rule

When changing a feature, update these files:

| Change Type | Required Docs |
|---|---|
| Architecture | `docs/ARCHITECTURE.md`, relevant Draw.io diagram |
| New agent | `docs/FEATURE_SPECIFICATION.md`, `docs/ARCHITECTURE.md` |
| New model provider | `docs/TECH_STACK.md`, `docs/ARCHITECTURE.md`, `.env.example` |
| New env var | `.env.example`, `docs/DEPLOYMENT_LOCAL.md`, `docs/DEPLOYMENT_PRODUCTION.md` |
| New database table | `docs/DATABASE_DESIGN.md` |
| New logger event | `docs/LOGGING_AND_OBSERVABILITY.md` |
| Edge-case fix | `docs/EDGE_CASES.md` |
| Any release | `CHANGELOG.md` |

## Coding Standards

Backend:

- Python 3.11+.
- FastAPI routers per module.
- Pydantic schemas.
- SQLAlchemy or SQLModel.
- Alembic migrations.
- Async where useful.
- Central config via environment variables.
- No secrets in code.

Frontend:

- Next.js app router.
- Tailwind CSS.
- Component-based dashboard.
- API client wrapper.
- Loading/error states on every page.
- Tables with filters/search/pagination.

Docker:

- Use multi-stage Dockerfiles.
- Separate dev/prod compose overrides.
- Use persistent volumes for databases and models.
- Use health checks.
- Use restart policies in production.

## Do Not Do

- Do not store raw API keys in logs.
- Do not send huge JSON into LLM prompts.
- Do not hardcode Gemini directly inside agents.
- Do not make agents call tools without allowlist checking.
- Do not allow infinite agent loops.
- Do not run long jobs inside normal HTTP request without queue support.
- Do not update code without updating docs.
- Do not mark unbuilt features as completed.
