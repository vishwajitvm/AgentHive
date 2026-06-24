# AgentHive System Architecture & Developer Testing Guide

> Detailed, layman-friendly + developer-focused guide for understanding, running, testing, debugging, and extending the AgentHive system.

---

# Table of Contents

1. [What AgentHive Is](#1-what-agenthive-is)
2. [High-Level Architecture](#2-high-level-architecture)
3. [Mental Model](#3-mental-model)
4. [Service URLs and Credentials](#4-service-urls-and-credentials)
5. [Docker Service Map](#5-docker-service-map)
6. [End-to-End Data Flow](#6-end-to-end-data-flow)
7. [Frontend: Next.js](#7-frontend-nextjs)
8. [Backend: FastAPI](#8-backend-fastapi)
9. [PostgreSQL Database](#9-postgresql-database)
10. [Redis Cache and Queue](#10-redis-cache-and-queue)
11. [Celery Worker](#11-celery-worker)
12. [MinIO Object Storage](#12-minio-object-storage)
13. [Ollama Local LLM](#13-ollama-local-llm)
14. [Prometheus Metrics](#14-prometheus-metrics)
15. [Loki Logs](#15-loki-logs)
16. [Grafana Dashboards](#16-grafana-dashboards)
17. [Developer Testing Guide](#17-developer-testing-guide)
18. [Common Debugging Scenarios](#18-common-debugging-scenarios)
19. [Advanced Testing Scenarios](#19-advanced-testing-scenarios)
20. [Production-Grade Missing Pieces](#20-production-grade-missing-pieces)
21. [Folder Structure Recommendation](#21-folder-structure-recommendation)
22. [Developer Verification Checklist](#22-developer-verification-checklist)

---

# 1. What AgentHive Is

AgentHive is an AI agent platform.

In simple words:

- User opens the website.
- User creates or uses an AI agent.
- User sends message, uploads file, or asks a task.
- Backend receives the request.
- Backend stores important information in database.
- Backend queues long-running work in Redis.
- Celery worker picks the work.
- Worker talks to Ollama or another LLM.
- Worker stores result.
- Frontend displays final answer.

In developer language:

AgentHive is a distributed full-stack application using:

- **Next.js** for frontend UI.
- **FastAPI** for REST APIs.
- **PostgreSQL** for persistent relational data.
- **Redis** as cache, queue broker, and temporary state store.
- **Celery** for async/background processing.
- **MinIO** for object/file storage.
- **Ollama** for local LLM inference.
- **Prometheus** for metrics scraping.
- **Loki** for log aggregation.
- **Grafana** for dashboards and observability.

---

# 2. High-Level Architecture

```mermaid
graph TD
    User(("User"))

    UI["Frontend UI<br/>Next.js :3000"]
    API["Backend API<br/>FastAPI :8000"]
    Worker["Celery Worker"]

    Postgres[("PostgreSQL<br/>:5432")]
    Redis[("Redis<br/>:6379")]
    MinIO[("MinIO<br/>API :9000<br/>Console :9001")]

    Ollama["Ollama LLM<br/>:11434"]

    Prometheus["Prometheus<br/>:9090"]
    Loki["Loki<br/>:3100"]
    Grafana["Grafana<br/>:3001"]

    User --> UI
    UI --> API

    API --> Postgres
    API --> Redis
    API --> MinIO

    Redis --> Worker
    Worker --> Postgres
    Worker --> MinIO
    Worker --> Ollama

    Prometheus -.scrapes.-> API
    Prometheus -.scrapes.-> Worker
    Prometheus -.scrapes.-> Docker

    Loki -.stores logs.-> API
    Loki -.stores logs.-> Worker

    Grafana --> Prometheus
    Grafana --> Loki
```

---

# 3. Mental Model

| Component | Layman Meaning | Developer Meaning |
|---|---|---|
| Frontend | Face of the app | Next.js client/server UI |
| Backend | Brain of the app | FastAPI REST API |
| PostgreSQL | Permanent notebook | Relational DB |
| Redis | Fast temporary memory | Cache + queue broker |
| Celery Worker | Background employee | Async task processor |
| MinIO | File cupboard | S3-compatible object storage |
| Ollama | AI brain | Local model inference server |
| Prometheus | Health collector | Metrics time-series DB |
| Loki | Log storage | Centralized log backend |
| Grafana | Monitoring TV | Dashboard and alerting UI |

---

# 4. Service URLs and Credentials

| Service | Browser URL | Internal Docker URL | Credentials |
|---|---|---|---|
| Frontend | `http://localhost:3000` | `http://frontend:3000` | None |
| Backend API | `http://localhost:8000/docs` | `http://api:8000` | Depends on auth |
| PostgreSQL | Not browser-based | `postgres:5432` | `agenthive / agenthive` |
| Redis | Not browser-based | `redis:6379` | No password by default |
| MinIO API | `http://localhost:9000` | `minio:9000` | `agenthive / agenthive123` |
| MinIO Console | `http://localhost:9001` | `minio:9001` | `agenthive / agenthive123` |
| Ollama | `http://localhost:11434` | `ollama:11434` | None |
| Grafana | `http://localhost:3001` | `grafana:3000` | `admin / admin` |
| Prometheus | `http://localhost:9090` | `prometheus:9090` | None |
| Loki | No normal UI | `loki:3100` | None |

Important:

- Browser can open HTTP apps only.
- Browser cannot directly open PostgreSQL `5432` or Redis `6379`.
- For PostgreSQL use DBeaver, pgAdmin, TablePlus, DataGrip, or `psql`.
- For Redis use RedisInsight or `redis-cli`.

---

# 5. Docker Service Map

## Start all services

```bash
docker compose up -d
```

## Stop all services

```bash
docker compose down
```

## Rebuild all services

```bash
docker compose up -d --build
```

## Check running containers

```bash
docker ps
```

Expected services:

```txt
agenthive-frontend
agenthive-api
agenthive-worker
agenthive-postgres
agenthive-redis
agenthive-minio
agenthive-ollama
agenthive-prometheus
agenthive-loki
agenthive-grafana
agenthive-promtail
```

Your actual names may be different. To find names:

```bash
docker ps --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"
```

## View all logs

```bash
docker compose logs -f
```

## View one service log

```bash
docker compose logs -f api
docker compose logs -f worker
docker compose logs -f frontend
docker compose logs -f postgres
docker compose logs -f redis
docker compose logs -f minio
docker compose logs -f ollama
```

## Restart one service

```bash
docker compose restart api
```

## Open shell inside container

```bash
docker exec -it agenthive-api bash
```

If bash is unavailable:

```bash
docker exec -it agenthive-api sh
```

---

# 6. End-to-End Data Flow

## Example: User asks agent to summarize PDF

### Step 1: User action

User opens:

```txt
http://localhost:3000
```

Then uploads a PDF and asks:

```txt
Summarize this PDF in simple language.
```

### Step 2: Frontend sends request

Frontend sends API request to backend.

Example:

```http
POST http://localhost:8000/api/files/upload
```

Then:

```http
POST http://localhost:8000/api/agents/{agent_id}/tasks
```

### Step 3: Backend receives request

Backend does:

1. Validates user.
2. Validates file.
3. Uploads file to MinIO.
4. Stores file metadata in PostgreSQL.
5. Creates task row in PostgreSQL.
6. Pushes task to Redis queue.
7. Returns task ID to frontend.

Example response:

```json
{
  "task_id": "task_123",
  "status": "queued",
  "message": "Task accepted and queued"
}
```

### Step 4: Redis holds task

Redis stores queue data temporarily.

Conceptually:

```txt
queue: celery
task: summarize_pdf
task_id: task_123
file_id: file_456
agent_id: agent_789
```

### Step 5: Celery worker picks task

Worker keeps watching Redis.

When task appears, worker picks it.

Worker does:

1. Reads task payload.
2. Gets file metadata from PostgreSQL.
3. Downloads file from MinIO.
4. Extracts text.
5. Builds LLM prompt.
6. Calls Ollama.
7. Saves answer into PostgreSQL.
8. Updates task status to completed.

### Step 6: Ollama generates response

Worker sends prompt to Ollama:

```json
{
  "model": "llama3",
  "prompt": "Summarize this extracted PDF text..."
}
```

Ollama returns generated summary.

### Step 7: Frontend checks task result

Frontend polls:

```http
GET http://localhost:8000/api/tasks/task_123
```

Response:

```json
{
  "task_id": "task_123",
  "status": "completed",
  "result": "This PDF explains..."
}
```

---

# 7. Frontend: Next.js

## 7.1 What Frontend Does

Frontend is the website.

It handles:

- Pages
- Buttons
- Forms
- Chat UI
- File upload UI
- Agent dashboard
- API calls
- Loading states
- Error messages

## 7.2 Frontend URL

```txt
http://localhost:3000
```

## 7.3 What to Check in Browser

Open DevTools:

```txt
F12 → Console
```

Check for:

```txt
- JavaScript errors
- API URL errors
- CORS errors
- hydration errors
- missing environment variables
```

Open Network tab:

```txt
F12 → Network
```

Then perform action:

```txt
- Login
- Create agent
- Send chat
- Upload file
```

Check:

```txt
Request URL
Request Method
Status Code
Payload
Response
```

## 7.4 Important Status Codes

| Status | Meaning | Where to Fix |
|---|---|---|
| 200 | OK | No issue |
| 201 | Created | No issue |
| 202 | Accepted/Queued | No issue |
| 400 | Bad request | Frontend payload or backend validation |
| 401 | Unauthorized | Auth/token issue |
| 403 | Forbidden | Permission/RBAC issue |
| 404 | Not found | Wrong API path |
| 409 | Conflict | Duplicate resource |
| 422 | Validation error | Pydantic schema mismatch |
| 500 | Server error | Backend code/logs |
| 502 | Gateway issue | Proxy/NGINX/backend down |
| 504 | Timeout | Long request should become Celery task |

## 7.5 Environment Variables

Example frontend `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=AgentHive
```

Inside Docker, sometimes frontend should still call browser-accessible backend:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Why?

Because frontend JavaScript runs in the user's browser. Browser cannot resolve Docker internal hostname like `api`.

Wrong:

```env
NEXT_PUBLIC_API_URL=http://api:8000
```

Right for browser:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 7.6 Common Frontend Issues

### Issue: Button click does nothing

Check:

- Is `onClick` attached?
- Is function called?
- Is API call happening in Network tab?
- Is button disabled?
- Is form preventing default incorrectly?

### Issue: CORS error

Browser console may show:

```txt
Access to fetch at http://localhost:8000 blocked by CORS policy
```

Fix in FastAPI CORS middleware.

Backend example:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: API URL undefined

Check:

```bash
docker compose logs -f frontend
```

Check `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Restart frontend after env change:

```bash
docker compose restart frontend
```

---

# 8. Backend: FastAPI

## 8.1 What Backend Does

Backend is the main controller.

It manages:

- API endpoints
- Validation
- Auth
- Database access
- Redis queue
- File upload
- Celery task creation
- Response formatting
- Error handling
- Metrics exposure

## 8.2 Backend URLs

```txt
Swagger: http://localhost:8000/docs
ReDoc:   http://localhost:8000/redoc
Health:  http://localhost:8000/health
Metrics: http://localhost:8000/metrics
```

## 8.3 Basic Health Test

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

Better health endpoint should check dependencies:

```json
{
  "status": "ok",
  "services": {
    "postgres": "ok",
    "redis": "ok",
    "minio": "ok",
    "ollama": "ok"
  }
}
```

## 8.4 Swagger Testing

Open:

```txt
http://localhost:8000/docs
```

Use Swagger for:

- Create user
- Login
- Create agent
- Upload file
- Start task
- Check task status
- Test chat endpoint

Example agent create request:

```json
{
  "name": "Research Agent",
  "description": "Reads files and answers questions",
  "model": "llama3",
  "tools": ["file_reader", "summarizer"]
}
```

## 8.5 Backend Environment Variables

Example:

```env
APP_ENV=local
API_HOST=0.0.0.0
API_PORT=8000

DATABASE_URL=postgresql://agenthive:agenthive@postgres:5432/agenthive

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=agenthive
MINIO_SECRET_KEY=agenthive123
MINIO_BUCKET=agenthive-uploads
MINIO_SECURE=false

OLLAMA_BASE_URL=http://ollama:11434

JWT_SECRET=change-me
JWT_ALGORITHM=HS256
```

Important:

- From inside Docker, backend connects to `postgres`, `redis`, `minio`, `ollama`.
- From host machine, you connect using `localhost`.

## 8.6 Typical Backend Folder Structure

```txt
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── logging.py
│   ├── api/
│   │   ├── routes_auth.py
│   │   ├── routes_agents.py
│   │   ├── routes_files.py
│   │   ├── routes_tasks.py
│   │   └── routes_health.py
│   ├── db/
│   │   ├── session.py
│   │   ├── models.py
│   │   └── migrations/
│   ├── services/
│   │   ├── redis_service.py
│   │   ├── minio_service.py
│   │   ├── ollama_service.py
│   │   └── agent_service.py
│   ├── workers/
│   │   ├── celery_app.py
│   │   └── tasks.py
│   └── schemas/
│       ├── user.py
│       ├── agent.py
│       ├── task.py
│       └── file.py
```

## 8.7 Common Backend Errors

### Database connection failed

Error:

```txt
could not connect to server: Connection refused
```

Check:

```bash
docker compose logs -f postgres
docker compose logs -f api
```

Fix:

```env
DATABASE_URL=postgresql://agenthive:agenthive@postgres:5432/agenthive
```

### Redis connection failed

Error:

```txt
Error connecting to Redis
```

Fix:

```env
REDIS_URL=redis://redis:6379/0
```

### MinIO access denied

Error:

```txt
InvalidAccessKeyId
SignatureDoesNotMatch
Access Denied
```

Fix credentials:

```env
MINIO_ACCESS_KEY=agenthive
MINIO_SECRET_KEY=agenthive123
```

### Ollama connection refused

Error:

```txt
Connection refused: ollama:11434
```

Fix:

```bash
docker compose restart ollama
curl http://localhost:11434/api/tags
```

---

# 9. PostgreSQL Database

## 9.1 What PostgreSQL Does

PostgreSQL stores permanent data.

In AgentHive, PostgreSQL should store:

- Users
- Sessions
- Agents
- Agent tools
- Conversations
- Messages
- Files metadata
- Tasks
- Tool execution logs
- Embedding metadata
- RAG document chunks
- Audit logs
- Billing/usage logs if needed

## 9.2 PostgreSQL Connection

Use DBeaver or pgAdmin.

```txt
Host: localhost
Port: 5432
Database: agenthive
Username: agenthive
Password: agenthive
```

Inside Docker:

```txt
Host: postgres
Port: 5432
```

## 9.3 Connect Using psql

From host if `psql` installed:

```bash
psql postgresql://agenthive:agenthive@localhost:5432/agenthive
```

From Docker:

```bash
docker exec -it agenthive-postgres psql -U agenthive -d agenthive
```

## 9.4 Basic PostgreSQL Commands

List databases:

```sql
\l
```

Connect database:

```sql
\c agenthive
```

List tables:

```sql
\dt
```

Describe table:

```sql
\d users
```

Exit:

```sql
\q
```

## 9.5 Useful SQL Queries

### See all tables

```sql
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

### Check users

```sql
SELECT id, email, created_at
FROM users
ORDER BY created_at DESC
LIMIT 20;
```

### Check agents

```sql
SELECT id, name, model, created_at
FROM agents
ORDER BY created_at DESC
LIMIT 20;
```

### Check conversations

```sql
SELECT id, user_id, agent_id, title, created_at
FROM conversations
ORDER BY created_at DESC
LIMIT 20;
```

### Check latest messages

```sql
SELECT id, conversation_id, role, LEFT(content, 100) AS preview, created_at
FROM messages
ORDER BY created_at DESC
LIMIT 20;
```

### Check uploaded files

```sql
SELECT id, user_id, filename, storage_key, mime_type, size_bytes, created_at
FROM files
ORDER BY created_at DESC
LIMIT 20;
```

### Check task status

```sql
SELECT id, task_type, status, error_message, created_at, updated_at
FROM tasks
ORDER BY created_at DESC
LIMIT 20;
```

### Check failed tasks

```sql
SELECT id, task_type, status, error_message, payload, created_at
FROM tasks
WHERE status = 'failed'
ORDER BY created_at DESC;
```

### Check slow/completed tasks

```sql
SELECT id, task_type, status, started_at, completed_at,
       EXTRACT(EPOCH FROM (completed_at - started_at)) AS duration_seconds
FROM tasks
WHERE completed_at IS NOT NULL
ORDER BY duration_seconds DESC
LIMIT 20;
```

## 9.6 What To Fix Where

| Problem | Where to Check | Where to Fix |
|---|---|---|
| User not created | `users` table | auth route/service |
| Agent not visible | `agents` table | frontend fetch or agents API |
| Chat missing | `messages` table | chat API or worker save logic |
| File uploaded but not shown | `files` table + MinIO | upload service |
| Task stuck queued | `tasks` table + Redis + worker | Celery/Redis/worker |
| Result not shown | `tasks.result` or `messages` | frontend polling/API response |

## 9.7 Recommended Tables

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agents (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name TEXT NOT NULL,
    description TEXT,
    model TEXT NOT NULL,
    system_prompt TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    agent_id UUID REFERENCES agents(id),
    title TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE files (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    filename TEXT NOT NULL,
    storage_key TEXT NOT NULL,
    mime_type TEXT,
    size_bytes BIGINT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    task_type TEXT NOT NULL,
    status TEXT NOT NULL,
    payload JSONB,
    result JSONB,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

# 10. Redis Cache and Queue

## 10.1 What Redis Does

Redis is fast temporary storage.

In AgentHive, Redis can be used for:

1. Celery broker.
2. Celery task result backend.
3. API cache.
4. Login/session cache.
5. Rate limiting.
6. WebSocket pub/sub.
7. Temporary upload state.
8. Agent execution locks.
9. Progress tracking.
10. Distributed task coordination.

Layman example:

PostgreSQL is like a permanent notebook.  
Redis is like a whiteboard.  
You write temporary fast things there.

## 10.2 Redis URL

```txt
localhost:6379
```

Inside Docker:

```txt
redis:6379
```

## 10.3 Connect With redis-cli

```bash
docker exec -it agenthive-redis redis-cli
```

Test:

```bash
PING
```

Expected:

```txt
PONG
```

## 10.4 Connect With RedisInsight

Install RedisInsight.

Connection:

```txt
Host: localhost
Port: 6379
Username: empty
Password: empty
```

In RedisInsight you can inspect:

- Keys
- Values
- TTL
- Streams
- Lists
- Hashes
- Pub/Sub
- Memory usage

## 10.5 Redis Key Types

| Type | Meaning | Example Use |
|---|---|---|
| String | Simple value | cache token |
| Hash | Object-like map | user session |
| List | Queue-like list | task queue |
| Set | Unique values | online users |
| Sorted Set | Ranked values | rate limits |
| Stream | Event log | live events |
| Pub/Sub | Real-time messages | websocket updates |

## 10.6 Basic Redis Commands

### See all keys

```bash
KEYS *
```

For production avoid `KEYS *`; use:

```bash
SCAN 0
```

### Get value

```bash
GET some:key
```

### Set value

```bash
SET test:name "AgentHive"
```

### Set value with expiry

```bash
SETEX cache:test 60 "hello"
```

This expires after 60 seconds.

### Check expiry

```bash
TTL cache:test
```

### Delete key

```bash
DEL cache:test
```

### Check memory

```bash
INFO memory
```

### Check clients

```bash
INFO clients
```

### Check stats

```bash
INFO stats
```

## 10.7 Celery-Related Redis Keys

Common Celery keys:

```txt
celery
_kombu.binding.celery
celery-task-meta-<task_id>
```

Check:

```bash
KEYS *celery*
```

Read task result:

```bash
GET celery-task-meta-<task_id>
```

Queue length:

```bash
LLEN celery
```

If queue length keeps increasing, worker is not processing.

## 10.8 Using Redis for Cache

Example cache key naming:

```txt
cache:user:{user_id}
cache:agent:{agent_id}
cache:conversation:{conversation_id}
cache:file:{file_id}
```

Example:

```bash
SETEX cache:agent:123 300 '{"name":"PDF Agent","model":"llama3"}'
GET cache:agent:123
TTL cache:agent:123
```

## 10.9 Using Redis for Rate Limiting

Example key:

```txt
rate_limit:user:{user_id}:minute
```

Commands:

```bash
INCR rate_limit:user:123:minute
EXPIRE rate_limit:user:123:minute 60
GET rate_limit:user:123:minute
```

Backend logic:

```txt
If count > 60, block request.
Else allow request.
```

## 10.10 Using Redis for Task Progress

Example key:

```txt
task_progress:{task_id}
```

Set progress:

```bash
HSET task_progress:task_123 status processing progress 40 message "Extracting PDF text"
```

Read progress:

```bash
HGETALL task_progress:task_123
```

Set expiry:

```bash
EXPIRE task_progress:task_123 3600
```

## 10.11 What To Check When Task Is Stuck

### Step 1: Check queue

```bash
docker exec -it agenthive-redis redis-cli LLEN celery
```

If output is high, worker is not consuming.

### Step 2: Check worker logs

```bash
docker compose logs -f worker
```

### Step 3: Check Redis keys

```bash
docker exec -it agenthive-redis redis-cli KEYS "*task*"
```

### Step 4: Check Postgres task table

```sql
SELECT id, status, error_message, created_at, updated_at
FROM tasks
ORDER BY created_at DESC
LIMIT 20;
```

## 10.12 Redis Common Problems

### Problem: Redis is running but no task processed

Possible reasons:

- Worker not running.
- Worker connected to wrong Redis DB.
- Celery queue name mismatch.
- Task import error.
- Task registered under different name.

Fix:

```bash
docker compose logs -f worker
docker compose restart worker
```

Check worker startup logs:

```txt
[tasks]
  . app.workers.tasks.summarize_pdf
  . app.workers.tasks.run_agent
```

If tasks not listed, import path is wrong.

### Problem: Cache not updating

Check key:

```bash
GET cache:agent:123
TTL cache:agent:123
```

Possible fix:

```bash
DEL cache:agent:123
```

Then retry frontend.

### Problem: Redis memory high

Check:

```bash
INFO memory
```

Find large keys using RedisInsight.

Possible fixes:

- Add TTL to cache keys.
- Delete old task result keys.
- Configure maxmemory policy.
- Do not store huge PDF text directly in Redis.

Recommended:

```txt
Store large file/text in MinIO or PostgreSQL.
Store only IDs/status in Redis.
```

---

# 11. Celery Worker

## 11.1 What Celery Worker Does

Worker handles background jobs.

Good for:

- LLM calls
- File parsing
- PDF extraction
- Embedding generation
- Long-running tool calls
- Scheduled agent tasks
- Email/WhatsApp sending
- Report generation

Bad for:

- Instant simple API validation
- Very small DB reads
- UI rendering

## 11.2 Why Not Do Everything in FastAPI?

Because LLM/file jobs can take seconds or minutes.

If backend waits:

- API request may timeout.
- User sees stuck UI.
- Server threads get blocked.
- Scaling becomes hard.

Correct flow:

```txt
FastAPI creates task → Redis queue → Worker processes → Frontend checks status
```

## 11.3 Worker Logs

```bash
docker compose logs -f worker
```

Expected logs:

```txt
Connected to redis://redis:6379/0
Task received
Task started
Task completed
```

## 11.4 Example Task Lifecycle

```txt
queued → started → processing → completed
```

Failure:

```txt
queued → started → failed
```

Retry:

```txt
queued → started → failed → retrying → completed
```

## 11.5 Example Celery Task

```python
from app.workers.celery_app import celery_app

@celery_app.task(bind=True, max_retries=3)
def summarize_pdf_task(self, task_id: str, file_id: str):
    try:
        # 1. update task started
        # 2. download file from MinIO
        # 3. extract text
        # 4. call Ollama
        # 5. save result in DB
        return {"status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)
```

## 11.6 Things You Can Do With Worker

- Run PDF summarizer.
- Generate embeddings.
- Crawl websites.
- Call tools.
- Run scheduled automations.
- Process files.
- Send notifications.
- Sync Google Drive.
- Run RAG indexing.
- Generate reports.
- Run multi-agent workflows.

## 11.7 Worker Debugging

### Check registered tasks

```bash
docker exec -it agenthive-worker celery -A app.workers.celery_app inspect registered
```

### Check active tasks

```bash
docker exec -it agenthive-worker celery -A app.workers.celery_app inspect active
```

### Check scheduled tasks

```bash
docker exec -it agenthive-worker celery -A app.workers.celery_app inspect scheduled
```

### Check reserved tasks

```bash
docker exec -it agenthive-worker celery -A app.workers.celery_app inspect reserved
```

### Purge queue

Careful, this deletes queued tasks:

```bash
docker exec -it agenthive-worker celery -A app.workers.celery_app purge
```

## 11.8 Common Worker Problems

| Problem | Reason | Fix |
|---|---|---|
| Task stuck queued | worker down | restart worker |
| Task not registered | import path issue | fix celery imports |
| Task fails immediately | exception in task code | check worker logs |
| Task retries forever | external service down | check MinIO/Ollama/Postgres |
| Worker memory high | loading large files/models | chunk files, avoid huge memory loads |
| Duplicate task execution | retry/idempotency issue | add task locking |

## 11.9 Worker Best Practices

- Store task status in PostgreSQL.
- Store progress in Redis.
- Store files in MinIO.
- Store only small payloads in Redis.
- Make tasks idempotent.
- Add retry limits.
- Add dead-letter handling.
- Add clear error messages.
- Add task timeout.
- Add logs with task ID.

---

# 12. MinIO Object Storage

## 12.1 What MinIO Does

MinIO stores files.

In AgentHive:

- PDF uploads
- Images
- CSV files
- Word docs
- Generated reports
- Agent output files
- Temporary files

PostgreSQL stores file metadata.  
MinIO stores actual file bytes.

Example:

PostgreSQL row:

```txt
file_id: file_123
filename: report.pdf
storage_key: users/123/files/report.pdf
bucket: agenthive-uploads
```

MinIO stores:

```txt
actual report.pdf file
```

## 12.2 MinIO URLs

Console:

```txt
http://localhost:9001
```

API:

```txt
http://localhost:9000
```

Credentials:

```txt
Username: agenthive
Password: agenthive123
```

## 12.3 What You Can Do in MinIO Console

Open console:

```txt
http://localhost:9001
```

You can:

- Create bucket.
- Upload file manually.
- Download file.
- Delete file.
- Check file path.
- Check file size.
- Check content type.
- Check access policy.
- Create access keys.
- Check object metadata.

## 12.4 Recommended Buckets

```txt
agenthive-uploads
agenthive-generated
agenthive-temp
agenthive-public
agenthive-rag-documents
```

## 12.5 Bucket Purpose

| Bucket | Purpose |
|---|---|
| `agenthive-uploads` | User-uploaded files |
| `agenthive-generated` | AI-generated files |
| `agenthive-temp` | Temporary processing files |
| `agenthive-public` | Public assets |
| `agenthive-rag-documents` | RAG source docs |

## 12.6 MinIO CLI

Install `mc` or use MinIO container if available.

Configure:

```bash
mc alias set local http://localhost:9000 agenthive agenthive123
```

List buckets:

```bash
mc ls local
```

Make bucket:

```bash
mc mb local/agenthive-uploads
```

List files:

```bash
mc ls local/agenthive-uploads
```

Upload file:

```bash
mc cp sample.pdf local/agenthive-uploads/test/sample.pdf
```

Download file:

```bash
mc cp local/agenthive-uploads/test/sample.pdf ./sample.pdf
```

Remove file:

```bash
mc rm local/agenthive-uploads/test/sample.pdf
```

## 12.7 What To Check When Upload Fails

### Step 1: Backend logs

```bash
docker compose logs -f api
```

### Step 2: MinIO logs

```bash
docker compose logs -f minio
```

### Step 3: Bucket exists

Open:

```txt
http://localhost:9001
```

Check bucket exists.

### Step 4: Database file row

```sql
SELECT id, filename, storage_key, bucket, created_at
FROM files
ORDER BY created_at DESC
LIMIT 20;
```

### Step 5: Object exists in MinIO

Go to bucket and search `storage_key`.

## 12.8 Common MinIO Problems

| Problem | Reason | Fix |
|---|---|---|
| Access denied | wrong key/secret | fix env |
| Bucket not found | bucket missing | create bucket on startup |
| File row exists but object missing | upload failed after DB insert | use transaction/rollback |
| Object exists but DB missing | DB insert failed after upload | cleanup orphan files |
| Browser opens 9000 weirdly | 9000 is API | use 9001 console |
| Large file fails | max size limit | increase backend/body limit |

## 12.9 Best Practice Upload Flow

Correct flow:

1. Validate file.
2. Generate unique storage key.
3. Upload to MinIO.
4. Save metadata to PostgreSQL.
5. Return file ID.

If database save fails after MinIO upload, delete MinIO object.

If MinIO upload fails, do not create DB row.

---

# 13. Ollama Local LLM

## 13.1 What Ollama Does

Ollama runs LLMs locally.

AgentHive can use it for:

- Chat
- Summarization
- Code explanation
- Document Q&A
- Tool planning
- Agent reasoning
- RAG answer generation

## 13.2 Ollama URL

```txt
http://localhost:11434
```

Open in browser.

Expected:

```txt
Ollama is running
```

## 13.3 Check Models

```bash
curl http://localhost:11434/api/tags
```

Expected:

```json
{
  "models": [
    {
      "name": "llama3:latest"
    }
  ]
}
```

## 13.4 Pull Model

From host:

```bash
ollama pull llama3
```

From Docker container:

```bash
docker exec -it agenthive-ollama ollama pull llama3
```

Other useful models:

```bash
ollama pull mistral
ollama pull qwen2.5
ollama pull deepseek-r1
ollama pull codellama
ollama pull nomic-embed-text
```

## 13.5 Generate Test

```bash
curl http://localhost:11434/api/generate \
-d '{
  "model": "llama3",
  "prompt": "Explain Redis in simple words",
  "stream": false
}'
```

## 13.6 Chat Test

```bash
curl http://localhost:11434/api/chat \
-d '{
  "model": "llama3",
  "messages": [
    {
      "role": "user",
      "content": "Explain AI agents in simple words"
    }
  ],
  "stream": false
}'
```

## 13.7 Embedding Test

For RAG you need embedding model:

```bash
ollama pull nomic-embed-text
```

Then:

```bash
curl http://localhost:11434/api/embeddings \
-d '{
  "model": "nomic-embed-text",
  "prompt": "AgentHive is an AI agent platform."
}'
```

## 13.8 What To Check When AI Response Fails

### Step 1: Ollama running?

```bash
curl http://localhost:11434
```

### Step 2: Model exists?

```bash
curl http://localhost:11434/api/tags
```

### Step 3: Backend uses correct URL?

Inside Docker:

```env
OLLAMA_BASE_URL=http://ollama:11434
```

From host:

```env
OLLAMA_BASE_URL=http://localhost:11434
```

### Step 4: Worker logs

```bash
docker compose logs -f worker
```

## 13.9 Common Ollama Problems

| Problem | Reason | Fix |
|---|---|---|
| Model not found | model not pulled | `ollama pull llama3` |
| Slow response | weak CPU/RAM | use smaller model |
| Connection refused | service down | restart Ollama |
| Out of memory | large model | use smaller quantized model |
| Bad answer | poor prompt/context | improve prompt/RAG |

## 13.10 Recommended Model Usage

| Use Case | Model |
|---|---|
| General chat | llama3 / mistral |
| Coding | codellama / deepseek-coder |
| Reasoning | deepseek-r1 |
| Embeddings | nomic-embed-text |
| Lightweight tasks | phi / small qwen |

---

# 14. Prometheus Metrics

## 14.1 What Prometheus Does

Prometheus collects numeric metrics.

Examples:

- API request count
- Error rate
- Response time
- CPU usage
- Memory usage
- Container health
- Queue length
- Worker task count

## 14.2 URL

```txt
http://localhost:9090
```

## 14.3 Basic Prometheus Query

Open Prometheus and run:

```promql
up
```

Meaning:

```txt
1 = target is up
0 = target is down
```

## 14.4 Useful Queries

### API request count

```promql
http_requests_total
```

### API request rate

```promql
rate(http_requests_total[5m])
```

### 500 errors

```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### Average latency

```promql
rate(http_request_duration_seconds_sum[5m])
/
rate(http_request_duration_seconds_count[5m])
```

### Container CPU

```promql
rate(container_cpu_usage_seconds_total[5m])
```

### Container memory

```promql
container_memory_usage_bytes
```

### Redis up

```promql
redis_up
```

### PostgreSQL up

```promql
pg_up
```

If exporters are not added yet, these metrics will not exist.

## 14.5 Missing Exporters To Add

For better monitoring, add:

- postgres-exporter
- redis-exporter
- node-exporter
- cadvisor
- celery-exporter
- minio metrics
- ollama metrics if available/custom

## 14.6 What To Fix Where

| Problem | Check | Fix |
|---|---|---|
| `up = 0` | Prometheus targets | service/network/metrics URL |
| No API metrics | `/metrics` endpoint | FastAPI prometheus middleware |
| No Docker metrics | cAdvisor | add cAdvisor container |
| No DB metrics | postgres exporter | add exporter |
| No Redis metrics | redis exporter | add exporter |

---

# 15. Loki Logs

## 15.1 What Loki Does

Loki stores logs from containers.

Examples:

- Backend error logs
- Worker task logs
- Redis logs
- PostgreSQL logs
- Ollama logs

You normally do not use Loki directly.

Use Grafana → Explore → Loki.

## 15.2 LogQL Examples

### All backend logs

```logql
{container="agenthive-api"}
```

### Backend errors

```logql
{container="agenthive-api"} |= "ERROR"
```

### Backend 500 errors

```logql
{container="agenthive-api"} |= "500"
```

### Worker task logs

```logql
{container="agenthive-worker"} |= "Task"
```

### Worker failures

```logql
{container="agenthive-worker"} |= "failed"
```

### Ollama logs

```logql
{container="agenthive-ollama"}
```

### Logs for specific task ID

```logql
{container=~"agenthive-api|agenthive-worker"} |= "task_123"
```

## 15.3 Recommended Logging Format

Use JSON logs:

```json
{
  "timestamp": "2026-06-24T10:00:00Z",
  "level": "INFO",
  "service": "worker",
  "task_id": "task_123",
  "message": "PDF summarization started"
}
```

Why?

Because you can filter logs better in Grafana.

---

# 16. Grafana Dashboards

## 16.1 URL

```txt
http://localhost:3001
```

Credentials:

```txt
Username: admin
Password: admin
```

## 16.2 What Grafana Shows

Grafana shows:

- Backend request rate.
- Backend error rate.
- API latency.
- Worker task success/failure.
- Redis queue length.
- PostgreSQL connections.
- MinIO storage.
- Ollama usage.
- Container CPU/RAM.
- Logs from Loki.

## 16.3 Add Data Sources

Go to:

```txt
Grafana → Connections → Data Sources
```

Add:

### Prometheus

```txt
URL: http://prometheus:9090
```

### Loki

```txt
URL: http://loki:3100
```

## 16.4 Useful Dashboards

Create dashboard panels:

1. API request rate.
2. API error rate.
3. Average response time.
4. Worker active tasks.
5. Failed tasks.
6. Redis queue length.
7. CPU per container.
8. Memory per container.
9. Backend error logs.
10. Worker error logs.

## 16.5 Example Panel Queries

### API request rate

```promql
rate(http_requests_total[5m])
```

### API error rate

```promql
rate(http_requests_total{status=~"5.."}[5m])
```

### Logs panel

```logql
{container="agenthive-api"} |= "ERROR"
```

## 16.6 Alerts To Add

Add alerts for:

- API down.
- Worker down.
- Redis down.
- PostgreSQL down.
- MinIO down.
- Ollama down.
- High 500 error rate.
- Queue length too high.
- Disk almost full.
- Memory usage high.

---

# 17. Developer Testing Guide

## 17.1 Full Local Startup Test

Run:

```bash
docker compose up -d --build
```

Check:

```bash
docker ps
```

Then open:

```txt
Frontend:    http://localhost:3000
Backend:     http://localhost:8000/docs
MinIO:       http://localhost:9001
Ollama:      http://localhost:11434
Prometheus:  http://localhost:9090
Grafana:     http://localhost:3001
```

## 17.2 Backend Dependency Test

Check health:

```bash
curl http://localhost:8000/health
```

Expected:

```json
{
  "status": "ok"
}
```

Advanced expected:

```json
{
  "status": "ok",
  "postgres": "ok",
  "redis": "ok",
  "minio": "ok",
  "ollama": "ok"
}
```

## 17.3 Database Test

```bash
docker exec -it agenthive-postgres psql -U agenthive -d agenthive
```

Then:

```sql
SELECT NOW();
\dt
```

## 17.4 Redis Test

```bash
docker exec -it agenthive-redis redis-cli
```

Then:

```bash
PING
KEYS *
INFO memory
```

## 17.5 MinIO Test

Open:

```txt
http://localhost:9001
```

Then:

1. Login.
2. Open bucket.
3. Upload sample PDF.
4. Download it.
5. Delete it.

## 17.6 Ollama Test

```bash
curl http://localhost:11434/api/tags
```

Generate:

```bash
curl http://localhost:11434/api/generate \
-d '{"model":"llama3","prompt":"Say hello","stream":false}'
```

## 17.7 Worker Test

Trigger a backend endpoint that creates Celery task.

Then check:

```bash
docker compose logs -f worker
```

Also check Redis:

```bash
docker exec -it agenthive-redis redis-cli LLEN celery
```

Also check Postgres:

```sql
SELECT id, status, error_message
FROM tasks
ORDER BY created_at DESC
LIMIT 10;
```

---

# 18. Common Debugging Scenarios

## 18.1 Frontend Shows Error

Check:

1. Browser console.
2. Browser network tab.
3. API response body.
4. Backend logs.

Commands:

```bash
docker compose logs -f frontend
docker compose logs -f api
```

## 18.2 API Gives 500

Check backend logs:

```bash
docker compose logs -f api
```

Common causes:

- Database error.
- Redis error.
- MinIO error.
- Ollama error.
- Python exception.
- Missing env variable.

## 18.3 Task Stuck in Queued

Check Redis:

```bash
docker exec -it agenthive-redis redis-cli LLEN celery
```

Check worker:

```bash
docker compose logs -f worker
```

Check DB:

```sql
SELECT id, task_type, status, error_message, created_at
FROM tasks
ORDER BY created_at DESC
LIMIT 20;
```

Fix:

```bash
docker compose restart worker
```

## 18.4 File Upload Works But AI Cannot Read File

Check:

1. File row in PostgreSQL.
2. Object exists in MinIO.
3. Worker can access MinIO.
4. File extraction library works.
5. Worker logs.

SQL:

```sql
SELECT id, filename, storage_key, bucket
FROM files
ORDER BY created_at DESC
LIMIT 10;
```

MinIO:

```txt
http://localhost:9001
```

## 18.5 AI Response Is Empty

Check:

1. Ollama model exists.
2. Prompt is not empty.
3. Extracted text is not empty.
4. Worker logs.
5. Ollama logs.

Commands:

```bash
curl http://localhost:11434/api/tags
docker compose logs -f worker
docker compose logs -f ollama
```

## 18.6 Redis Cache Has Old Data

Check key:

```bash
GET cache:agent:123
TTL cache:agent:123
```

Clear:

```bash
DEL cache:agent:123
```

Clear all Redis carefully:

```bash
FLUSHDB
```

Dangerous because it deletes all keys in current DB.

## 18.7 PostgreSQL Data Looks Wrong

Check migrations:

```bash
alembic current
alembic history
```

Check table:

```sql
\d table_name
```

Check recent records:

```sql
SELECT *
FROM table_name
ORDER BY created_at DESC
LIMIT 20;
```

---

# 19. Advanced Testing Scenarios

## 19.1 Stop Ollama and Test Failure Handling

```bash
docker compose stop ollama
```

Now run AI task.

Expected:

- Task should fail gracefully.
- Frontend should show useful error.
- Worker should log Ollama connection issue.
- Task status should become failed.

Restart:

```bash
docker compose start ollama
```

## 19.2 Stop Redis and Test Queue Failure

```bash
docker compose stop redis
```

Create task.

Expected:

- Backend should return queue error.
- Worker should disconnect.
- Logs should show Redis unavailable.

Restart:

```bash
docker compose start redis
```

## 19.3 Stop PostgreSQL and Test DB Failure

```bash
docker compose stop postgres
```

Call backend.

Expected:

- Health check should show DB down.
- API should return controlled error.
- No silent failure.

Restart:

```bash
docker compose start postgres
```

## 19.4 Stop MinIO and Test Upload Failure

```bash
docker compose stop minio
```

Upload file.

Expected:

- Upload fails clearly.
- No broken DB row.
- Error logged.

Restart:

```bash
docker compose start minio
```

## 19.5 Load Test API

Install k6 or use simple curl loop.

Simple test:

```bash
for i in {1..50}; do curl -s http://localhost:8000/health; done
```

Better with k6:

```js
import http from 'k6/http';

export default function () {
  http.get('http://localhost:8000/health');
}
```

Run:

```bash
k6 run test.js
```

---

# 20. Production-Grade Missing Pieces

## 20.1 Security

Add:

- JWT access token.
- Refresh token rotation.
- Password hashing using Argon2 or bcrypt.
- RBAC roles.
- API rate limit.
- Request size limit.
- File type validation.
- Virus scanning.
- Secure CORS.
- Secrets manager.
- Audit logs.

## 20.2 Reliability

Add:

- Health checks for every service.
- Retry logic.
- Dead-letter queue.
- Task timeout.
- Idempotent task design.
- Database backups.
- MinIO backups.
- Redis persistence if needed.
- Graceful shutdown.

## 20.3 AI/RAG

Add:

- Embedding model.
- Vector database or pgvector.
- Chunking pipeline.
- RAG retrieval.
- Source citations.
- Prompt templates.
- Tool calling framework.
- Multi-agent orchestration.
- Model fallback.
- Token usage tracking.

## 20.4 Observability

Add:

- Structured JSON logs.
- Request ID.
- Task ID in logs.
- User ID in audit logs.
- Prometheus exporters.
- Grafana dashboards.
- Alerts.
- Error tracking like Sentry.

## 20.5 DevOps

Add:

- `.env.example`
- Makefile.
- CI/CD.
- Unit tests.
- Integration tests.
- Docker health checks.
- Staging environment.
- Production compose/Kubernetes.
- NGINX reverse proxy.
- SSL certificates.

---

# 21. Folder Structure Recommendation

Recommended docs:

```txt
docs/
├── architecture/
│   ├── 01-system-overview.md
│   ├── 02-developer-testing-guide.md
│   ├── 03-database-and-storage-guide.md
│   ├── 04-redis-celery-worker-guide.md
│   ├── 05-ai-ollama-rag-guide.md
│   ├── 06-observability-monitoring-guide.md
│   ├── 07-production-deployment-guide.md
│   └── MASTER_ARCHITECTURE_GUIDE.md
├── api/
│   ├── auth-api.md
│   ├── agents-api.md
│   ├── files-api.md
│   └── tasks-api.md
├── testing/
│   ├── local-testing-checklist.md
│   ├── integration-testing.md
│   └── failure-testing.md
└── troubleshooting/
    ├── frontend-issues.md
    ├── backend-issues.md
    ├── redis-worker-issues.md
    ├── minio-issues.md
    └── ollama-issues.md
```

---

# 22. Developer Verification Checklist

| Area | Check | Command/URL | Expected |
|---|---|---|---|
| Frontend | UI loads | `http://localhost:3000` | Page opens |
| Backend | Swagger loads | `http://localhost:8000/docs` | Docs open |
| Health | API health | `curl /health` | status ok |
| PostgreSQL | DB connects | `psql` / DBeaver | tables visible |
| Redis | Redis alive | `PING` | PONG |
| Redis Queue | Queue length | `LLEN celery` | not stuck |
| Worker | Logs | `docker compose logs -f worker` | tasks processed |
| MinIO | Console | `http://localhost:9001` | login works |
| Ollama | Model list | `/api/tags` | models visible |
| Prometheus | Targets | `up` | 1 |
| Loki | Logs | Grafana Explore | logs visible |
| Grafana | Dashboard | `http://localhost:3001` | panels visible |

---

# Final Practical Rule

Whenever something breaks, follow this chain:

```txt
Frontend issue?
→ Check browser console
→ Check network request
→ Check backend logs
→ Check database/redis/minio/ollama
→ Check worker logs
→ Check Grafana/Loki
```

For task/agent issues:

```txt
Frontend → Backend → PostgreSQL task row → Redis queue → Worker → MinIO/Ollama → PostgreSQL result → Frontend
```

That is the full AgentHive debugging path.
