# Production Deployment

## Goal

Run AgentHive in a stable production-like Docker environment.

## Production Principles

- No hot reload.
- Use optimized builds.
- Use restart policies.
- Use health checks.
- Use persistent volumes.
- Keep secrets outside Git.
- Backup PostgreSQL and MinIO.
- Monitor logs and metrics.

## Start Production

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Production Services

| Service | Role |
|---|---|
| nginx | Public reverse proxy |
| frontend | Built Next.js frontend |
| backend | FastAPI app behind Gunicorn/Uvicorn |
| worker | Background agent jobs |
| scheduler | Scheduled jobs |
| postgres | Main database + pgvector |
| redis | Queue/cache |
| minio | File storage |
| ollama | Local model runtime |
| loki | Logs |
| prometheus | Metrics |
| grafana | Dashboards |

## CI/CD Approach

Recommended flow:

```text
Push to GitHub
  -> Run tests
  -> Build frontend image if frontend changed
  -> Build backend image if backend changed
  -> Deploy only changed services
  -> Run migrations
  -> Check health endpoints
```

## Deployment Safety

Before deployment:

- Run tests.
- Validate environment variables.
- Backup database.
- Backup MinIO if needed.
- Check migration plan.

After deployment:

- Check `/health`.
- Check `/ready`.
- Check worker logs.
- Check Grafana dashboards.
- Check model provider health.

## Scaling

Scale workers:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --scale worker=3
```

Scale backend behind Nginx only after Nginx upstream config supports multiple backend instances.

## Backup Plan

PostgreSQL:

```bash
docker exec agenthive-postgres pg_dump -U agenthive agenthive > backup.sql
```

MinIO:

Use MinIO client or volume-level backup.

## Production Edge Cases

| Edge Case | Handling |
|---|---|
| Backend crash | restart policy + logs |
| Worker crash | restart policy + dead-letter jobs |
| Redis down | readiness check fails, queue paused |
| PostgreSQL down | API returns controlled error |
| Ollama down | fallback provider or controlled error |
| Gemini quota exceeded | fallback to Ollama |
| Disk full | alerts and retention policies |
