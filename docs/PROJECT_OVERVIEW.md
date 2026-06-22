# AgentHive Project Overview

AgentHive is a dashboard-controlled platform for deploying many AI agents that can work alone or together.

## Problem AgentHive Solves

Most AI bots are isolated. Users must manually choose a model, write prompts, copy data between tools, and repeat setup for every workflow. AgentHive solves this by creating one central platform where agents, tools, models, workflows, logs, and environment settings are managed from a dashboard.

## Main Users

1. Developers who want coding, debugging, documentation, and testing agents.
2. Students who want PDF, research, notes, and study agents.
3. Working professionals who want email, calendar, task, and reminder agents.
4. Small teams that want internal automations without expensive SaaS tools.

## Design Principles

- Free-first: prefer self-hosted and open-source services.
- Docker-first: every core service must run in Docker.
- Dashboard-first: configuration should be controlled from UI.
- Provider-agnostic: agents should not depend on only one LLM.
- Token-efficient: use compact context formats when talking to LLMs.
- Observable: every important action must be logged and traceable.
- Versioned: agents, prompts, workflows, and docs must be versioned.

## Main Components

| Component | Responsibility |
|---|---|
| Dashboard | Manage agents, models, tools, workflows, logs, settings |
| Backend API | Authentication, CRUD APIs, orchestration endpoints |
| Agent Orchestrator | Selects agents and coordinates execution |
| LLM Router | Chooses model provider and handles fallback |
| Tools Layer | File, PDF, search, storage, code, external integrations |
| Workflow Engine | Runs multi-step agent automations |
| PostgreSQL | Primary relational storage |
| pgvector | Vector memory for agents and documents |
| Redis | Queue, cache, rate limit, temporary state |
| MinIO | File/object storage |
| Ollama | Local LLM fallback runtime |
| Observability | Logs, metrics, traces, dashboard visibility |
