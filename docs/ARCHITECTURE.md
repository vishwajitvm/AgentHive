# AgentHive Architecture

## Architecture Style

Use a modular monolith that is microservice-ready.

Start with one backend project, but keep modules clean enough to split later.

```text
backend/app/
  api/
  agents/
  llm/
  tools/
  workflows/
  memory/
  jobs/
  logging/
```

> **Developer Note**: For a complete list of testing URLs and detailed data flow instructions, please read the [SYSTEM ARCHITECTURE AND TESTING GUIDE](file:///c:/python/AgentHive/docs/SYSTEM_ARCHITECTURE_AND_TESTING_GUIDE.md).

## High-Level Data Flow

```mermaid
graph TD
    classDef frontend fill:#3b82f6,stroke:#1d4ed8,stroke-width:2px,color:#fff
    classDef backend fill:#10b981,stroke:#047857,stroke-width:2px,color:#fff
    classDef db fill:#f59e0b,stroke:#b45309,stroke-width:2px,color:#fff
    classDef ai fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#fff
    classDef obs fill:#f97316,stroke:#c2410c,stroke-width:2px,color:#fff

    User(("User"))
    UI["Frontend UI (Next.js :3000)"]:::frontend
    API["Backend API (FastAPI :8000)"]:::backend
    Worker["Celery Worker"]:::backend
    
    Postgres[("PostgreSQL (:5432)")]:::db
    Redis[("Redis Cache (:6379)")]:::db
    MinIO[("MinIO Storage (:9000)")]:::db
    
    Ollama["Ollama LLM (:11434)"]:::ai
    
    Grafana["Grafana (:3001)"]:::obs
    Prometheus["Prometheus (:9090)"]:::obs
    Loki["Loki (:3100)"]:::obs

    User -- "Clicks UI" --> UI
    UI -- "REST API" --> API
    API -- "Queues Task" --> Redis
    Redis -- "Picks up Task" --> Worker
    
    API -- "Reads/Writes" --> Postgres
    Worker -- "Reads/Writes" --> Postgres
    
    API -- "Uploads Files" --> MinIO
    Worker -- "Reads Files" --> MinIO
    
    Worker -- "Sends Prompts" --> Ollama
    
    Prometheus -. "Scrapes Metrics" .-> API
    Loki -. "Aggregates Logs" .-> API
    Grafana -. "Visualizes" .-> Prometheus
    Grafana -. "Visualizes" .-> Loki
```

## Main Request Flow

1. User sends request from dashboard.
2. Nginx forwards request to FastAPI.
3. FastAPI creates request ID and trace ID.
4. Agent Orchestrator receives task.
5. Orchestrator selects the correct agent or workflow.
6. Agent loads config, prompt version, tool permissions, memory settings.
7. LLM Router selects primary model.
8. Model Policy Engine checks token budget, provider health, rate limits.
9. Provider Adapter calls Gemini or fallback model.
10. Tool calls run if allowed.
11. Every step is logged.
12. Final result returns to dashboard.
13. Agent run timeline is visible in logs UI.

## Agent Runtime

Agents must not directly call Gemini, GPT, Ollama, or Hugging Face. Agents call the LLM Router.

Correct:

```text
Agent -> LLMRouter -> ProviderAdapter -> Model
```

Wrong:

```text
Agent -> Gemini directly
```

## LLM Fallback Policy

Default:

```text
Primary: Gemini
Secondary: Ollama
Fallback order: Gemini -> Ollama -> Hugging Face -> Groq -> GPT
```

Fallback triggers:

- Token limit exceeded.
- Quota exceeded.
- Provider timeout.
- Provider health check failed.
- Invalid model response.
- Dashboard policy disallows primary provider for this request.

## Data Flow

- Structured app data goes to PostgreSQL.
- Vector embeddings go to pgvector.
- Temporary state and job queues go to Redis.
- Files go to MinIO.
- Raw container logs go to Loki.
- Important business logs go to PostgreSQL.
- Metrics go to Prometheus.
- Dashboards are shown through Grafana and AgentHive UI.

## Scalability Plan

Start:

```text
One frontend container
One backend container
One worker container
One scheduler container
One PostgreSQL
One Redis
One MinIO
One Ollama
```

Scale later:

```text
Multiple backend containers
Multiple worker containers
Separate workflow service
Separate tool execution service
Separate LLM gateway service
Separate observability stack
GPU machine for Ollama
Kubernetes if required
```
