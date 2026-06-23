# Verification Commands & Process

This file lists the shell commands used to verify the deployment, check the status of services, test the API endpoints, and check the agent execution and fallback loops.

---

## 1. Shell Commands Run for Verification

### A. Deploy Container Infrastructure
Starts the full multi-agent stack (Next.js, FastAPI, Celery, Postgres, Redis, MinIO, Ollama, Loki, Prometheus, Grafana) in hot-reloading development mode:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build
```

### B. Verify Running Containers
Checks the state, status, and ports of all 12 services:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml ps
```

### C. Backend Health & Readiness Check
Invokes the `/ready` health route to check backend health and connectivity to Postgres, Redis, MinIO, and Ollama:
```bash
curl http://localhost:8000/ready
```

### D. List Registered Agents
Retrieves the list of default pre-populated agents from the database:
```bash
# PowerShell
Invoke-RestMethod -Uri http://localhost:8000/api/agents -Method Get | Format-Table id, slug, name

# Bash
curl -s http://localhost:8000/api/agents | jq '.[] | {id: .id, slug: .slug, name: .name}'
```

### E. Trigger Agent Run (Sync)
Triggers a synchronous execution of the Personal Assistant Agent to verify the LLM Router and active policy fallbacks:
```bash
# PowerShell
Invoke-RestMethod -Uri http://localhost:8000/api/agents/1/run -Method Post -ContentType "application/json" -Body '{"query": "hello"}'

# Bash
curl -X POST http://localhost:8000/api/agents/1/run -H "Content-Type: application/json" -d '{"query": "hello"}'
```

### F. Check Backend Application Logs
Tails backend logs to verify step executions, API calls, and model router fallback operations:
```bash
docker logs --tail 150 agenthive-backend
```

### G. Pull Local LLM Model
Downloads the default local LLM model inside the Ollama container:
```bash
docker exec agenthive-ollama ollama pull llama3
```

---

## 2. Documentation and Changes Process

Whenever a feature, database schema, workflow, environment variable, or deployment configuration changes in the codebase, the following documentation update process must be followed:

1. **Keep Code and Docs Synchronized**: Never change implementation without updating documentation.
2. **File Mapping for Changes**:
   - **Architecture & Flow**: Update [docs/ARCHITECTURE.md](file:///c:/python/AgentHive/docs/ARCHITECTURE.md) and related diagrams.
   - **New Agent Profile**: Update [docs/FEATURE_SPECIFICATION.md](file:///c:/python/AgentHive/docs/FEATURE_SPECIFICATION.md).
   - **Model Providers & Stack**: Update [docs/TECH_STACK.md](file:///c:/python/AgentHive/docs/TECH_STACK.md) and `.env.example`.
   - **Environment Configurations**: Update [docs/DEPLOYMENT_LOCAL.md](file:///c:/python/AgentHive/docs/DEPLOYMENT_LOCAL.md), [docs/DEPLOYMENT_PRODUCTION.md](file:///c:/python/AgentHive/docs/DEPLOYMENT_PRODUCTION.md), and `.env.example`.
   - **Database Tables/Fields**: Update [docs/DATABASE_DESIGN.md](file:///c:/python/AgentHive/docs/DATABASE_DESIGN.md).
   - **Logging & Monitoring Events**: Update [docs/LOGGING_AND_OBSERVABILITY.md](file:///c:/python/AgentHive/docs/LOGGING_AND_OBSERVABILITY.md).
   - **Edge Cases & Workarounds**: Update [docs/EDGE_CASES.md](file:///c:/python/AgentHive/docs/EDGE_CASES.md).
3. **Record in Changelog**: Add the modification details to [CHANGELOG.md](file:///c:/python/AgentHive/CHANGELOG.md) under the corresponding version header (e.g. `[0.2.0-MVP]`).
