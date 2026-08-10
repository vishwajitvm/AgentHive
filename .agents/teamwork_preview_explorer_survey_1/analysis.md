# Technical Exploration Report: AgentHive Multi-Agent & Orchestration Architecture

**Author**: `teamwork_preview_explorer_survey_1`  
**Date**: 2026-08-08 (UTC)  
**Target System**: AgentHive Codebase (`c:\python\AgentHive`)

---

## Executive Summary
This report provides a comprehensive architectural survey of the existing AgentHive platform, evaluating its backend design, LLM routing layer, agent execution engine, tool registry, and workflow capabilities. It identifies key extension points and details the exact architectural upgrades needed to implement **Requirement 1 (R1: Multi-Agent Orchestration Engine)** with dynamic routing, smart fallback, and latency-optimized multi-LLM execution.

---

## 1. Existing Architecture & Codebase Map

### 1.1 Repository & Backend Structure
The AgentHive backend is built using **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL**, **Celery** (with Redis broker), **MinIO**, and **Grafana Loki**.

Key backend directories and files:
```
backend/
├── app/
│   ├── main.py                  # FastAPI app initialization, middleware, routes
│   ├── agents/
│   │   ├── base.py              # BaseAgent execution loop (ReAct loop, tool parser)
│   │   ├── models.py            # Agent, AgentVersion, Prompt, PromptVersion models
│   │   ├── orchestrator.py      # AgentOrchestrator service (run execution & versioning)
│   │   ├── registry.py          # Agent initialization
│   │   └── seeder.py            # Agent seeding helper
│   ├── api/
│   │   ├── health.py            # Health check endpoint
│   │   └── routes/
│   │       ├── agents.py        # CRUD & execution endpoints for agents
│   │       ├── auth.py          # Auth endpoints
│   │       ├── logs.py          # Execution logs endpoints
│   │       ├── models.py        # Provider & Model Policy endpoints
│   │       ├── settings.py      # Settings endpoints
│   │       ├── tools.py         # Tools listing endpoints
│   │       ├── upload.py        # File upload endpoints
│   │       └── workflows.py    # Workflow DAG CRUD & execution endpoints
│   ├── core/
│   │   ├── config.py            # Pydantic Settings (env vars, provider defaults)
│   │   ├── database.py          # Async engine & sessionmaker
│   │   ├── exceptions.py        # Custom exceptions
│   │   ├── security.py          # Secret encryption/decryption
│   │   └── toon.py              # Token/Context compression helpers
│   ├── jobs/
│   │   └── worker.py            # Celery task definitions (execute_agent_run, execute_workflow_run)
│   ├── llm/
│   │   ├── models.py            # ModelProvider, ModelPolicy database models
│   │   ├── policy.py            # Active policy retrieval and defaulting
│   │   ├── router.py            # LLMRouter (sequential provider fallback)
│   │   └── providers/
│   │       ├── base.py          # Base LLM provider abstract class
│   │       ├── gemini.py        # Gemini adapter (httpx REST / SDK)
│   │       ├── groq.py          # Groq adapter (httpx REST / SDK)
│   │       ├── huggingface.py   # HuggingFace adapter
│   │       ├── ollama.py        # Local Ollama REST adapter
│   │       └── openai.py        # OpenAI REST/SDK adapter
│   ├── logging/
│   │   └── logger.py            # Structlog logging configuration
│   ├── logs/
│   │   ├── models.py            # AgentRun, AgentStep, ToolCall, LLMCall models
│   │   └── service.py           # Log query service
│   ├── memory/
│   │   ├── embeddings.py        # Vector embedding generator
│   │   ├── models.py            # Memory item models
│   │   └── vector_store.py      # PgVector memory store
│   ├── tools/
│   │   ├── base.py              # BaseTool abstract class
│   │   ├── models.py            # Tool database model
│   │   ├── registry.py          # ToolRegistry & built-in tool implementations
│   │   └── seeder.py            # Tool seeder
│   └── workflows/
│       ├── engine.py            # WorkflowExecutor (DAG topological execution engine)
│       └── models.py            # Workflow, WorkflowRun, WorkflowStep models
```

---

## 2. Existing Execution Flow & Component Analysis

### 2.1 Single Agent Execution Loop (`BaseAgent` & `AgentOrchestrator`)
1. **Invocation**: A client triggers an agent run via `POST /api/agents/{agent_id}/run` (synchronous or background via Celery `agenthive.execute_agent_run`).
2. **Orchestration**: `AgentOrchestrator.execute_run()` in `backend/app/agents/orchestrator.py`:
   - Retrieves active `Agent` and `PromptVersion`.
   - Injects optional retrieved vector memory context (`vector_store.search_memories`).
   - Creates or reuses an `AgentVersion` snapshot and initializes an `AgentRun` log entry (`status="running"`).
   - Instantiates `BaseAgent` (`backend/app/agents/base.py`).
3. **ReAct Reasoning Loop**: `BaseAgent.run()` executes sequentially up to `max_steps` or `timeout_seconds`:
   - Formats conversation history using TOON compression (`format_agent_context`).
   - Delegates prompt completion to `llm_router.generate()`.
   - Parses response using regex for `[TOOL] tool_slug | {"arg": "val"}` or `[ANSWER] {"reasoning": ..., "confidence_score": ..., "answer": ...}`.
   - If a tool call is detected: validates against `allowed_tools`, looks up tool in `tool_registry` (`backend/app/tools/registry.py`), executes `tool.run(**kwargs)`, summarizes output using TOON (`summarize_tool_result`), appends `ToolCall` and `AgentStep` logs, and feeds observation back into history.
   - If answer is detected: breaks loop, updates `AgentRun` to `"completed"`, stores output in database, and saves memory.

### 2.2 Existing LLM Provider Router (`LLMRouter`)
- Located in `backend/app/llm/router.py`.
- Supports 5 provider adapters (`gemini`, `ollama`, `openai`, `huggingface`, `groq`).
- Reads the active `ModelPolicy` (default fallback chain: `gemini,ollama,huggingface,groq,openai`).
- **Sequential Execution & Fallback**:
  - Tries primary provider -> retries up to `retry_count`.
  - On failure, moves to next provider in fallback chain.
  - Logs `LLMCall` records with token estimates, status, and latency.
- **Current Limitation**: LLM execution is purely single-threaded sequential. There is no parallel speculative call ("LLM racing"), low-latency tiering, or ensemble voting.

### 2.3 Existing Multi-Agent Capabilities (`WorkflowExecutor`)
- Located in `backend/app/workflows/engine.py`.
- Operates on static **DAG definitions** (`definition_json` containing fixed `nodes` and `edges`).
- Validates DAG using Kahn's topological sort (`validate_dag`).
- Node types supported:
  - `agent`: Invokes `orchestrator.execute_run()` with input template interpolation (e.g. `{input}`, `{node_1.output}`).
  - `condition`: Safe string evaluation via `eval()`.
  - `approval`: Pauses run (`status="waiting_approval"`) until manual user resume endpoint is called.
- **Current Limitation**: Workflows require pre-defined static DAG nodes and edges. There is no dynamic query classification, auto-agent selection, supervisor routing, or swarm peer handoff.

---

## 3. Required Upgrades for R1 (Multi-Agent Orchestration Engine)

To meet Requirement 1 (R1), AgentHive requires upgrading from static single-agent/fixed-DAG execution to a high-performance **Multi-Agent Orchestration Engine** with dynamic routing and latency-optimized multi-LLM execution.

### 3.1 Dynamic Routing Architecture Patterns

We recommend implementing a unified **Multi-Agent Routing Engine** supporting three core interaction patterns:

1. **Hierarchical / Supervisor Pattern**:
   - A high-speed **Supervisor Agent** inspects the user query, breaks down multi-part tasks into sub-goals, delegates sub-tasks to specialized domain agents (e.g. Search Agent, Developer Agent, Fact Checker, Data Analyst), collects sub-agent results, and synthesizes a final unified answer.
2. **Swarm / Peer Handoff Pattern**:
   - Lightweight autonomous agent handoffs where an agent can transfer control or request assistance from another specialized agent when its allowed tools are insufficient.
3. **Smart Router / Direct Fallback Pattern**:
   - High-speed intent classifier (keyword/regex rules or low-latency LLM call via Groq/Gemini Flash) routes single-intent queries directly to the target specialized agent, bypassing supervisor overhead for minimal latency.

### 3.2 Multi-LLM Execution & Latency Optimization

1. **Parallel Multi-LLM Racing / Speculative Execution**:
   - Implement `generate_fastest()` / `generate_parallel()` in `LLMRouter`.
   - Dispatches prompt concurrently to top-N healthy providers (e.g., Gemini Flash + Groq LLaMA3 + Ollama local) using `asyncio.as_completed()` or `asyncio.wait()`.
   - Returns the first valid response received, cancelling remaining slow background tasks to achieve minimum possible latency.
2. **Tiered Model Selection Policy**:
   - **Fast Tier (Classifier/Router)**: Uses Groq or Gemini 1.5 Flash for rapid intent routing (<300ms).
   - **Execution Tier (Specialized Agents)**: Uses domain-specific providers/prompts for tool calls.
   - **Synthesis Tier (Supervisor)**: Uses high-reasoning models (e.g. OpenAI GPT-4o / Gemini Pro) for synthesizing complex multi-agent results.
3. **Smart Provider Fallback**:
   - Automatic circuit breaking: temporarily skips providers experiencing high error rates or latency spikes.

---

## 4. Proposed Code Organization & Extension Points

To implement R1 cleanly without breaking existing APIs or database schemas, the following code modifications are recommended:

### 4.1 New & Modified Files

| Target File | Purpose / Modifications Required |
|---|---|
| `backend/app/agents/multi_agent.py` *(New)* | Core `MultiAgentEngine` implementing Supervisor, Swarm, and Router patterns. |
| `backend/app/llm/router.py` *(Modify)* | Add `generate_parallel()` / `generate_race()` for concurrent multi-LLM execution with latency optimization. |
| `backend/app/agents/orchestrator.py` *(Modify)* | Integrate dynamic routing mode option into `execute_run()`. |
| `backend/app/api/routes/orchestration.py` *(New)* | New REST API router `/api/orchestrate` for multi-agent dynamic routing execution and mode selection. |
| `backend/app/api/routes/agents.py` *(Modify)* | Update `/run` endpoint to support `mode="direct" \| "supervisor" \| "swarm" \| "auto"`. |
| `backend/app/core/config.py` *(Modify)* | Add configuration flags for default routing mode, parallel LLM racing timeout, and primary routing provider. |

### 4.2 Class & Interface Extension Details

#### 1. Multi-Agent Engine (`backend/app/agents/multi_agent.py`)
```python
class MultiAgentEngine:
    async def route_and_execute(
        self,
        query: str,
        db: AsyncSession,
        mode: str = "auto", # "auto", "supervisor", "swarm", "direct"
        agent_ids: List[int] = None
    ) -> Dict[str, Any]:
        # 1. Intent Classification / Routing Decision
        # 2. Execution under chosen pattern (Supervisor / Swarm / Direct)
        # 3. Output Synthesis & Trace Generation
        pass
```

#### 2. Latency-Optimized Multi-LLM Call (`backend/app/llm/router.py`)
```python
async def generate_parallel(
    self,
    prompt: str,
    providers: List[str] = ["gemini", "groq", "ollama"],
    db: AsyncSession = None,
    timeout: float = 30.0
) -> str:
    # Race top active providers concurrently via asyncio.wait(..., return_when=FIRST_COMPLETED)
    # Cancel remaining pending calls and return fastest successful result.
    pass
```

---

## 5. Summary & Next Steps
- The existing AgentHive backend provides a robust FastAPI/SQLAlchemy framework with individual agent ReAct loops, static workflow DAGs, and sequential LLM fallback.
- **R1 implementation** requires building the `MultiAgentEngine` (`multi_agent.py`), extending `LLMRouter` with parallel racing execution (`generate_parallel`), and adding dynamic routing routes in FastAPI.
- These additions directly lay the groundwork for expanding tools/agents (R2) and creating the architecture documentation and `.drawio` diagram (R3).
