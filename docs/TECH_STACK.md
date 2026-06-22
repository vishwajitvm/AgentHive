# AgentHive Tech Stack

## Frontend

Use Next.js, React, TypeScript, and Tailwind CSS.

Why:

- Professional dashboard structure.
- Fast local development with hot reload.
- Strong component ecosystem.
- Easy route-based pages.
- Good future support for authentication and server-side rendering if needed.

## Backend

Use Python FastAPI.

Why:

- Good async API support.
- Automatic OpenAPI documentation.
- Strong Python ecosystem for agents, LLMs, embeddings, and document processing.
- Clean separation of routers, services, schemas, and workers.

## Database

Use PostgreSQL with pgvector.

Why:

- Stores users, agents, workflows, runs, logs, models, prompts, tools.
- pgvector adds vector memory without needing a separate paid vector database.
- Reliable and production proven.

## Cache and Queue

Use Redis.

Why:

- Celery broker.
- Temporary agent state.
- Rate limiting.
- Caching provider health and model status.
- Idempotency keys.

## Workers

Use Celery.

Why:

- Long-running agent jobs should not block HTTP requests.
- Scheduled tasks and workflows can run in background.
- Workers can scale separately from API.

## File Storage

Use MinIO.

Why:

- Free S3-compatible local object storage.
- Good for PDFs, uploaded files, generated reports, logs archive.
- Can be swapped with S3 later if needed.

## LLM Providers

Default policy:

1. Gemini primary.
2. Ollama secondary/fallback.
3. Hugging Face optional fallback.
4. Groq optional fallback.
5. GPT optional paid fallback.
6. Custom provider for OpenAI-compatible endpoints.

## Prompt and Context Format

Use JSON for APIs and storage. Use TOON or compact key-value text for LLM prompts.

Reason:

- APIs need strict machine-readable JSON.
- LLM context should be token efficient.
- Large JSON wastes tokens when sent to model.

## Observability

Use:

- Structlog or Loguru for structured application logs.
- OpenTelemetry for traces.
- Loki for log storage.
- Promtail for log collection.
- Prometheus for metrics.
- Grafana for dashboards.

## Deployment

Use Docker Compose first.

Later migration path:

- Docker Compose -> Docker Swarm or Kubernetes.
- PostgreSQL managed/self-hosted.
- Redis managed/self-hosted.
- MinIO or S3.
- Ollama on GPU server if needed.
