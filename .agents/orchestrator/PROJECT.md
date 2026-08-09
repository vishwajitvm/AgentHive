# PROJECT: AgentHive Multi-Agent Orchestration Architecture

## Architecture
AgentHive is an AI agent orchestration system built with FastAPI, SQLAlchemy Async, Celery, PostgreSQL (pgvector), Redis, and Docker.
This project upgrades AgentHive to a state-of-the-art multi-agent framework featuring:
- **Multi-Agent Orchestration Engine (`MultiAgentEngine`)**: Implements Hierarchical/Supervisor (task breakdown & worker delegation), Swarm (peer handoffs), and Router (fast intent classification to specialized agent) patterns.
- **Speculative Parallel Multi-LLM Router (`LLMRouter.generate_parallel`)**: Concurrent provider racing across Gemini, Ollama, OpenAI, Groq, HuggingFace for minimal response latency.
- **Categorized Tool Architecture (`backend/app/tools/modules/`)**: 40 zero-cost & local library tools across Web, Document, Text, Utility, and Developer categories registered in `ToolRegistry`.
- **Specialized Agents Portfolio**: Portfolio of 30 core specialized agents (General Assistant, Web Search, Data Analyst, Fact Checker, Code Architect, System Debugger, Document Processor, NLP Specialist, DevSecOps, etc.) mapped to specialized toolsets.
- **Automated Testing Suite & Infrastructure**: Unit/Integration test suites (`backend/tests/` - 32 tests passing) + updated Docker Compose & environment configs.
- **Architecture Documentation & Draw.io Diagram**: Updated `docs/ARCHITECTURE.md`, `docs/FEATURE_SPECIFICATION.md`, `docs/SYSTEM_ARCHITECTURE_AND_TESTING_GUIDE.md`, `README.md`, and a valid XML `.drawio` diagram in `docs/architecture.drawio` & `docs/diagrams/multi-agent-architecture.drawio`.

## Feature Inventory
| # | Feature | Description | Milestone | Source | Status |
|---|---------|-------------|-----------|--------|--------|
| 1 | Multi-Agent Orchestration Engine | `MultiAgentEngine` supporting Hierarchical, Swarm, and Router patterns | M1 | R1 | DONE |
| 2 | Speculative Multi-LLM Racing | `LLMRouter.generate_parallel()` concurrent LLM querying | M1 | R1 | DONE |
| 3 | Dynamic Orchestration Endpoints | API endpoint `/api/orchestrate` and extended `/api/agents/{id}/run` | M1 | R1 | DONE |
| 4 | Modular Tool Sub-modules | Split tools into `backend/app/tools/modules/` (web, doc, text, utility, dev) | M2 | R2 | DONE |
| 5 | Web Tools Expansion (9 tools) | Wikipedia, ArXiv, RSS, Weather, DNS, WHOIS, HackerNews, GitHub, URL Checker | M2 | R2 | DONE |
| 6 | Document Tools Expansion (5 tools) | Docx, Excel Writer, PPTX, OCR, JSON/YAML validator & converter | M2 | R2 | DONE |
| 7 | Text/NLP Tools Expansion (5 tools) | Sentiment Analysis, Text Summarizer, Text Diff, Keyword Extractor, Markdown to HTML | M2 | R2 | DONE |
| 8 | Utility Tools Expansion (5 tools) | Calculator, Datetime, Image Metadata, Hash/Crypto, Zip Archiver | M2 | R2 | DONE |
| 9 | Developer Tools Expansion (3 tools) | Git Tool, SQL Query Builder, JSON Schema Validator | M2 | R2 | DONE |
| 10 | Agent Portfolio Expansion | Specialized agents registration (General Assistant, Web Search, Data Analyst, Fact Checker, etc.) | M3 | R2 | DONE |
| 11 | Agent & Tool DB Seeder | Auto-seed database tools and agents on startup (`seed_elite_agents.py`, `seeder.py`) | M3 | R2 | DONE |
| 12 | Environment & Docker Configs | Updated `requirements.txt`, `.env.example`, Dockerfiles, `docker-compose.yml` | M4 | R2 | DONE |
| 13 | Markdown Architecture Documentation | Updated `docs/ARCHITECTURE.md` and related system specs | M5 | R3 | DONE |
| 14 | Architecture Draw.io Diagram | Valid XML `.drawio` diagram in `docs/architecture.drawio` | M5 | R3 | DONE |
| 15 | Automated Unit & Integration Tests | Pytest test suite in `backend/tests/unit/` and `backend/tests/integration/` | M6 | Verification | DONE |
| 16 | Docker Build & Run Verification | Verify backend container builds and runs clean without dependency issues | M6 | Verification | DONE |

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| M1 | Core Multi-Agent Engine & LLM Racing | `MultiAgentEngine`, `generate_parallel`, `/api/orchestrate` | None | DONE |
| M2 | Massive Tool Expansion | 27+ new tools (40 total) across Web, Doc, Text, Utility, Dev in `backend/app/tools/modules/` | None | DONE |
| M3 | Agent Expansion & Registration | Seed 30 specialized agents mapped to expanded tool slugs | M1, M2 | DONE |
| M4 | Configs & Docker Integration | `requirements.txt`, `.env.example`, Dockerfiles, `docker-compose.yml` | M2 | DONE |
| M5 | Documentation & Draw.io Diagram | Updated `docs/ARCHITECTURE.md` and `docs/architecture.drawio` | M1, M2, M3 | DONE |
| M6 | Automated Testing & E2E Verification | Pytest unit/integration test suite (32 tests pass) + Docker verification | M1-M5 | DONE |

## Interface Contracts
### `MultiAgentEngine` ↔ `BaseAgent` / `LLMRouter`
- `MultiAgentEngine.execute_orchestration(pattern: str, prompt: str, agent_ids: List[str], db: AsyncSession)`
- `LLMRouter.generate_parallel(prompt: str, providers: List[str], timeout: float)`
- Tool execution interface: `BaseTool.run(**kwargs) -> str`

## Code Layout
- `backend/app/agents/multi_agent.py`: Multi-agent orchestration engine
- `backend/app/llm/router.py`: Extended LLM router with speculative racing
- `backend/app/api/routes/orchestrator.py`: Dynamic orchestration REST API routes
- `backend/app/tools/modules/`: Categorized tool implementation modules
- `backend/app/tools/registry.py`: Centralized tool registry aggregation (40 registered tools)
- `backend/seed_elite_agents.py`: Specialized agent seed definitions (30 core specialized agents)
- `backend/requirements.txt`: Python package dependencies
- `docs/ARCHITECTURE.md`: Technical architecture documentation
- `docs/architecture.drawio`: Draw.io architecture diagram XML
- `backend/tests/`: Pytest unit and integration test suite (32 tests passing)
