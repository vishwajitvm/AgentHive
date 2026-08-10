# Change Log — Milestone 1 (M1)

## Summary of Changes

Milestone 1 implements the Core Multi-Agent Orchestration Engine and Speculative Parallel LLM Racing for AgentHive.

---

### 1. New Multi-Agent Orchestration Engine (`backend/app/agents/multi_agent.py`)
- Created `MultiAgentEngine` supporting three dynamic orchestration interaction patterns:
  - **Hierarchical / Supervisor Pattern (`execute_supervisor`)**:
    - Analyzes complex multi-intent requests and decomposes them into specialized sub-tasks assigned to domain subagents (e.g. `web_search_agent`, `data_analyst`, `fact_checker_agent`, `system_debugger`).
    - Dispatches sub-tasks to specialized subagents via `orchestrator.execute_run()`.
    - Synthesizes completed sub-agent outputs into a unified, coherent response.
  - **Swarm Pattern (`execute_swarm`)**:
    - Executes dynamic agent-to-agent handoff loop.
    - Inspects agent outputs for `[HANDOFF] agent_slug | {context}` tags to dynamically transfer execution control to another agent.
    - Loops until an agent produces a final `[ANSWER]` response or reaches `max_handoffs`.
  - **Router Pattern (`execute_router`)**:
    - Intent classification router that inspects user prompt against candidate agent capabilities and tools.
    - Selects the single best specialized agent and executes execution directly.
  - **Auto Dispatcher (`orchestrate`)**:
    - Automatically classifies requests to supervisor, swarm, or router patterns dynamically.

---

### 2. Speculative Parallel LLM Racing (`backend/app/llm/router.py`)
- Upgraded `LLMRouter` with `async def generate_parallel(...)`:
  - Queries multiple configured LLM providers (e.g., Gemini, Groq, Ollama) concurrently using `asyncio.wait(..., return_when=FIRST_COMPLETED)`.
  - Pre-resolves provider API keys and models sequentially to avoid SQLAlchemy `AsyncSession` concurrency conflicts.
  - Returns the fastest non-error response for speculative latency optimization.
  - Automatically cancels pending slower calls.
  - Logs winning `LLMCall` record to database.

---

### 3. Application Configuration Upgrades (`backend/app/core/config.py`)
- Added settings for default orchestration pattern, parallel LLM racing toggle, timeout, and default racing providers (`default_orchestration_pattern`, `parallel_llm_racing_enabled`, `parallel_llm_timeout_seconds`, `parallel_llm_default_providers`).

---

### 4. REST API Routes (`backend/app/api/routes/orchestrator.py` & `backend/app/api/routes/agents.py`)
- Created `backend/app/api/routes/orchestrator.py`:
  - Exposed `POST /api/orchestrate` endpoint accepting `MultiAgentRequest` (prompt, pattern, target_agents, initial_agent, use_parallel_llm, max_handoffs) and returning `MultiAgentResponse`.
- Extended `POST /api/agents/{agent_id}/run` in `backend/app/api/routes/agents.py`:
  - Updated `RunPayload` to include `multi_agent_mode`, `target_agents`, and `use_parallel_llm`.
  - Invokes `multi_agent_engine.orchestrate(...)` when `multi_agent_mode` is set and != "direct".
- Registered `orchestrator_router` in `backend/app/main.py`.

---

### 5. Automated Testing Suite (`backend/tests/test_multi_agent.py`)
- Created comprehensive pytest unit test suite covering:
  - `test_generate_parallel_fastest_wins`: Verifies speculative racing selects fastest provider.
  - `test_generate_parallel_error_fallback`: Verifies error resilience during racing.
  - `test_multi_agent_router_pattern`: Verifies intent classification & agent routing.
  - `test_multi_agent_supervisor_pattern`: Verifies query decomposition, subagent execution, and synthesis.
  - `test_multi_agent_swarm_pattern_handoff`: Verifies dynamic `[HANDOFF]` tag extraction and handoff chain execution.
  - `test_orchestrate_api_endpoint`: Verifies `/api/orchestrate` REST API response.
