# Changes Log — Milestone 6 (M6)

## Overview
Milestone 6 implements a comprehensive automated unit and integration pytest test suite and verifies the end-to-end Docker containerization setup for AgentHive.

## Files Created & Modified

### 1. Test Suite Infrastructure
- `backend/tests/conftest.py`:
  - Configured `sys.path` dynamically so `app` package is automatically discovered.
  - Implemented `MockAsyncSession` and `MockExecuteResult` to simulate SQLAlchemy AsyncSession behavior without external DB dependency.
  - Created reusable fixtures: `mock_db_session`, `sample_prompts`, and `sample_agents`.
- `backend/tests/unit/__init__.py`: Package initialization for unit tests.
- `backend/tests/integration/__init__.py`: Package initialization for integration tests.

### 2. Multi-Agent Engine Unit Tests
- `backend/tests/unit/test_multi_agent_engine.py`:
  - Added unit test `test_get_candidate_agents_all`: Verifies retrieving active candidate agents.
  - Added unit test `test_get_candidate_agents_filtered`: Verifies filtering by agent slug, name, or ID.
  - Added unit test `test_get_candidate_agents_fallback`: Verifies fallback behavior on empty candidate match.
  - Added unit test `test_router_single_candidate`: Verifies direct execution when only 1 candidate agent is available.
  - Added unit test `test_router_json_classification`: Verifies LLM intent classification parsing JSON responses and markdown blocks (` ```json `).
  - Added unit test `test_router_regex_fallback`: Verifies regex extraction fallback for non-standard JSON LLM output.
  - Added unit test `test_router_no_candidates_raises_error`: Verifies `AgentRunError` is raised when candidate pool is empty.
  - Added unit test `test_supervisor_pattern_breakdown_and_synthesis`: Verifies query breakdown into subtasks, subagent execution, and final response synthesis.
  - Added unit test `test_supervisor_fallback_to_router_on_json_error`: Verifies graceful fallback to router pattern if subtask decomposition fails.
  - Added unit test `test_swarm_pattern_dynamic_handoff_chain`: Verifies agent-to-agent dynamic handoff loop with `[HANDOFF]` tags and context transfer.
  - Added unit test `test_swarm_pattern_max_handoffs_limit`: Verifies enforcement of safety handoff ceiling (`max_handoffs`).
  - Added unit test `test_orchestrate_auto_mode_classification`: Verifies pattern classification when `pattern="auto"`.

### 3. LLM Router & Parallel Racing Unit Tests
- `backend/tests/unit/test_llm_router_parallel.py`:
  - Added unit test `test_generate_parallel_fastest_wins`: Verifies concurrent provider racing (`generate_parallel()`), where the fastest provider response wins and slower pending calls are cancelled.
  - Added unit test `test_generate_parallel_error_resilience`: Verifies skipping failing providers and returning output from healthy providers.
  - Added unit test `test_generate_parallel_all_providers_fail_raises_error`: Verifies `LLMRouteError` exception handling when all providers fail.
  - Added unit test `test_generate_parallel_timeout_handling`: Verifies handling provider timeouts.
  - Added unit test `test_generate_sequential_fallback`: Verifies standard fallback order execution in `LLMRouter.generate()`.

### 4. Registered Tools Unit Tests
- `backend/tests/unit/test_all_40_tools.py`:
  - Added test `test_registry_contains_all_40_tools`: Verifies all 40 tools (13 original core + 9 Web + 5 Document + 5 Text + 5 Utility + 3 Developer) are registered in `ToolRegistry` and have valid metadata.
  - Added test `test_all_40_tools_instantiate_and_run`: Verifies that all 40 tools instantiate cleanly and execute `.run()` with valid non-empty string responses.

### 5. Specialized Agents Seeder Unit Tests
- `backend/tests/unit/test_specialized_agents_seeder.py`:
  - Added test `test_specialized_agents_structure_and_tool_mapping`: Verifies that all 30 specialized agents exist in `SPECIALIZED_AGENTS` and that every tool in `tools_enabled` maps to a valid tool in `ToolRegistry`.
  - Added test `test_upsert_specialized_agents_seeding`: Verifies database upsert operations for inserting and updating agent definitions.

### 6. Orchestration & Agent REST API Integration Tests
- `backend/tests/integration/test_api_orchestrate.py`:
  - Added integration test `test_orchestrate_endpoint_success`: Verifies `POST /api/orchestrate` returns HTTP 200 with structured JSON response.
  - Added integration test `test_orchestrate_endpoint_error_handling`: Verifies HTTP 500 error handling on backend failure.
  - Added integration test `test_agent_run_endpoint_direct`: Verifies `POST /api/agents/{id}/run` in direct mode.
  - Added integration test `test_agent_run_endpoint_multi_agent_delegation`: Verifies `POST /api/agents/{id}/run` delegating to `MultiAgentEngine` for swarm/supervisor modes.
  - Added integration test `test_agent_run_endpoint_not_found`: Verifies HTTP 404 response for invalid agent ID.

### 7. Docker Infrastructure Verification
- Verified `docker-compose.yml`: Services configured for Postgres (pgvector), Redis, MinIO, Ollama, Loki, Prometheus, Grafana, Promtail, Keycloak.
- Verified `docker-compose.dev.yml`: Live reload setup for frontend, backend, Celery worker, and scheduler.
- Verified `docker-compose.prod.yml`: Production Gunicorn + Uvicorn workers and Nginx reverse proxy configuration.
- Verified `backend/Dockerfile`: Multi-stage build (base, dev, prod) with system packages (`tesseract-ocr`, `poppler-utils`, `libmagic1`, `git`, `curl`).
