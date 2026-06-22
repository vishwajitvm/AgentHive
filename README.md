# AgentHive

AgentHive is a free-first, Docker-first multi-agent platform for creating, deploying, monitoring, and managing multiple AI agents from one advanced dashboard.

The platform is designed for users who want to run many agent bots together, switch LLM providers from the dashboard, keep token usage low, and observe every action an agent performs.

## Project Goals

1. Build a scalable agent platform, not a single chatbot.
2. Use free and self-hostable services wherever possible.
3. Run the full system with Docker in local development and production.
4. Support multiple LLM providers: Gemini, GPT, Ollama, Hugging Face, Groq, and custom OpenAI-compatible APIs.
5. Use Gemini as the default primary model, with dashboard-controlled fallback to Ollama or other providers.
6. Use TOON or compact key-value prompts for LLM context to reduce token usage.
7. Keep frontend/backend API communication stable using JSON, but avoid sending large JSON into LLM prompts.
8. Log everything professionally: API calls, agent runs, steps, tool calls, model calls, fallbacks, errors, latency, token usage, and workflow transitions.
9. Make all major configuration manageable from the dashboard instead of changing code repeatedly.
10. Maintain docs version-wise and update docs whenever any feature changes.

## Recommended Stack

| Area | Technology | Reason |
|---|---|---|
| Frontend | Next.js + React + Tailwind CSS | Professional dashboard, routing, components, fast development |
| Backend | Python FastAPI | Fast APIs, async support, agent orchestration, clean docs |
| Database | PostgreSQL | Reliable relational data for agents, users, logs, workflows |
| Vector Memory | pgvector | Free vector memory inside PostgreSQL |
| Queue/Cache | Redis | Celery queue, cache, rate limits, temporary state |
| Workers | Celery | Background agent runs, scheduled jobs, long-running tasks |
| Storage | MinIO | Free S3-compatible local file storage |
| Local LLM | Ollama | Free local fallback model runtime |
| Primary LLM | Gemini | Default free/low-cost cloud model option |
| Prompt Format | TOON + compact key-value | Lower LLM token usage than large JSON |
| Reverse Proxy | Nginx | Production routing, TLS termination, static/proxy split |
| Monitoring | Prometheus + Grafana | Metrics and dashboards |
| Logs | Loki + Promtail | Container and application log aggregation |
| Tracing | OpenTelemetry | Request and agent execution traces |
| Deployment | Docker Compose first, Kubernetes later | Easy local/prod parity, scalable later |

## High-Level Flow

```text
User Dashboard
  -> Nginx
  -> FastAPI Backend
  -> Agent Orchestrator
  -> Agent Registry
  -> LLM Router
  -> Model Policy Engine
  -> Provider Adapter
  -> Gemini / Ollama / Hugging Face / GPT
  -> Tool Layer
  -> PostgreSQL / pgvector / Redis / MinIO
  -> Observability Layer
```

## Important Rule for Future AI Builders

Whenever a feature, architecture decision, database table, workflow, agent behavior, environment variable, or deployment process changes, update the matching documentation in `/docs` and update `CHANGELOG.md`.

Do not change implementation only. Documentation must stay synchronized with code.

## Repository Structure

```text
AgentHive/
  README.md
  AI_BUILD_GUIDE.md
  CHANGELOG.md
  .gitignore
  .env.example
  docker-compose.yml
  docker-compose.dev.yml
  docker-compose.prod.yml
  backend/
  frontend/
  infra/
  scripts/
  docs/
    PROJECT_OVERVIEW.md
    TECH_STACK.md
    ARCHITECTURE.md
    FEATURE_SPECIFICATION.md
    LOGGING_AND_OBSERVABILITY.md
    DEPLOYMENT_LOCAL.md
    DEPLOYMENT_PRODUCTION.md
    EDGE_CASES.md
    DATABASE_DESIGN.md
    VERSIONING_POLICY.md
    AgentHive_Project_Documentation.docx
    diagrams/
```

## MVP Build Order

1. Docker foundation.
2. Backend health API.
3. Frontend dashboard shell.
4. PostgreSQL and Redis connection.
5. Agent CRUD APIs.
6. Model provider CRUD APIs.
7. LLM Router with Gemini primary and Ollama fallback.
8. Agent run endpoint.
9. Professional structured logging.
10. Agent run dashboard.
11. Tool system.
12. Workflow executor.
13. Monitoring with Grafana/Loki/Prometheus.

## Running Locally

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

After first build, normal code changes should hot reload:

- Frontend changes reload through Next.js dev server.
- Backend changes reload through `uvicorn --reload`.
- Worker changes restart through file watcher.

## Production Run

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

Production should use optimized images, no hot reload, health checks, restart policies, and persistent volumes.
