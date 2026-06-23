# Changelog

All notable changes to AgentHive must be documented here.

## [0.2.0-MVP] - 2026-06-22

### Added
- Complete Docker Compose development and production infrastructure configurations (postgres, redis, minio, loki, promtail, prometheus, grafana, backend, frontend, celery worker, celery scheduler).
- FastAPI backend modules (health ready checks, agents CRUD, model config API, fallback policy resolver, workflow engine, log analytics).
- Encrypted secrets table for API keys utilizing Fernet symmetric cryptography keys.
- Token optimization formatting system using TOON tags for prompt context compression.
- pgvector semantic memory support mapped to SQLAlchemy.
- Celery worker background tasks executing agent loop steps and workflow executions.
- Direct REST HTTP providers adapters for Gemini, Ollama, OpenAI, Groq, and Hugging Face.
- Premium glassmorphic Next.js dashboard visualizer displaying telemetry stats, success cards, custom SVG token charts, chat consoles, and step activity trace timelines.

## [0.1.0] - Planning Package

### Added

- Project README.
- AI build guide for Antigravity, Codex, Claude, and similar tools.
- Detailed architecture documentation.
- Feature-wise specification.
- Local and production deployment documentation.
- Logging and observability plan.
- Edge-case handling plan.
- Database design overview.
- Draw.io diagrams for backend, frontend, database, Redis/cache, LLM routing, developer deployment, request/data flow, and full system architecture.
- Starter backend and frontend folder structures.
- Docker Compose planning files.

### Notes

- This version is documentation and scaffold oriented.
- Implementation must follow the phase order in `AI_BUILD_GUIDE.md`.
