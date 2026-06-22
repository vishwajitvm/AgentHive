# Local Deployment

## Goal

Run the complete AgentHive system locally using Docker.

## Prerequisites

- Docker Desktop or Docker Engine.
- Docker Compose.
- Minimum 8 GB RAM recommended.
- More RAM recommended if running Ollama models locally.

## First Setup

```bash
cp .env.example .env
```

Then edit `.env` only if needed.

## Start Development Environment

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

## Hot Reload Behavior

Frontend:

```text
Change files in frontend/ -> Next.js reloads automatically.
```

Backend:

```text
Change files in backend/ -> Uvicorn reloads automatically.
```

Worker:

```text
Change Python worker files -> watchmedo restarts Celery worker.
```

## Local URLs

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| Backend Docs | http://localhost:8000/docs |
| MinIO Console | http://localhost:9001 |
| Ollama | http://localhost:11434 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| Loki | http://localhost:3100 |

## Common Commands

```bash
# Stop containers
docker compose down

# Stop and remove volumes - destructive
docker compose down -v

# View backend logs
docker logs -f agenthive-backend

# View worker logs
docker logs -f agenthive-worker

# Enter backend container
docker exec -it agenthive-backend bash
```

## Ollama Model Setup

After Ollama starts:

```bash
docker exec -it agenthive-ollama ollama pull llama3.1
```

## Troubleshooting

| Issue | Fix |
|---|---|
| Port already in use | Change ports in compose or stop conflicting service |
| Backend cannot connect DB | Check postgres health and DATABASE_URL |
| Ollama model missing | Pull model inside Ollama container |
| Frontend not hot reloading | Ensure volume mount and polling env are set |
| Worker not restarting | Check watchmedo is installed in backend image |
