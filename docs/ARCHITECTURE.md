# AgentHive Technical Architecture Specification

> **Comprehensive Technical Architecture Guide for AgentHive Multi-Agent Orchestration, Speculative LLM Racing, 40-Tool Catalog, REST APIs, and Observability Infrastructure.**

---

## 1. Architectural Overview & System Design

AgentHive is a enterprise-grade, distributed AI agent platform designed to orchestrate complex multi-agent workflows, minimize LLM inference latency through speculative racing, and execute sandboxed operations across a modular 40-tool catalog.

The system is built as a microservice-ready modular architecture:

```text
backend/app/
├── agents/         # MultiAgentEngine (Supervisor, Swarm, Router) & BaseAgent ReAct loop
├── api/            # FastAPI REST routes (/api/orchestrate, /api/agents/{id}/run, etc.)
├── core/           # Database, security, exceptions, and TOON prompt context engine
├── jobs/           # Celery background worker tasks and task queues
├── llm/            # LLMRouter with speculative parallel racing across 5 LLM providers
├── logging/        # Structured JSON logger & OpenTelemetry tracing integrations
├── logs/           # Database persistence for AgentRun, Step, ToolCall, LLMCall logs
├── tools/          # ToolRegistry & 5 sub-module categories (Web, Doc, Text, Utility, Dev)
└── workflows/      # Directed workflow execution graphs
```

---

## 2. Multi-Agent Orchestration Engine (`MultiAgentEngine`)

Located in `backend/app/agents/multi_agent.py`, the `MultiAgentEngine` manages dynamic task execution across three primary multi-agent orchestration patterns, plus an automated intent classification classifier (`pattern="auto"`).

```
                        ┌──────────────────────────────┐
                        │   User Request / Prompt     │
                        └──────────────┬───────────────┘
                                       │
                         ┌─────────────▼──────────────┐
                         │   MultiAgentEngine         │
                         │   pattern classification   │
                         └──────┬──────┬──────┬───────┘
                                │      │      │
           ┌────────────────────┘      │      └────────────────────┐
           ▼                           ▼                           ▼
┌──────────────────────┐    ┌────────────────────┐    ┌─────────────────────────┐
│ Supervisor Pattern   │    │ Swarm Pattern      │    │ Router Pattern          │
│ • Decompose subtasks │    │ • Peer Handoffs    │    │ • Intent Classification │
│ • Delegate to agents │    │ • [HANDOFF] tag    │    │ • Single Agent Execute  │
│ • Synthesize output  │    │ • Loop until solved│    │ • Fallback handling     │
└──────────────────────┘    └────────────────────┘    └─────────────────────────┘
```

### 2.1 Hierarchical / Supervisor Pattern (`execute_supervisor`)

1. **Decomposition Phase**: The engine passes the user prompt and active agent portfolio descriptions to an LLM supervisor prompt. The LLM breaks down the request into a JSON structure of discrete sub-tasks, assigning each to the optimal specialized sub-agent slug.
2. **Worker Delegation Phase**: For each sub-task in sequence, `MultiAgentEngine` invokes `orchestrator.execute_run()` using the targeted sub-agent's configuration and tools.
3. **Synthesis Phase**: The engine formats all sub-agent execution outputs into a unified context prompt and queries the LLM to synthesize a cohesive final answer for the user.

### 2.2 Dynamic Swarm Pattern (`execute_swarm`)

1. **Peer Control Transfers**: Agents execute in a peer-to-peer loop where any agent can hand off execution control to another specialized agent by prepending a `[HANDOFF] target_slug | {"context": "..."}` tag to its output.
2. **Context Propagation**: The handoff context and historical output are forwarded to the target agent as its initial prompt for the next step.
3. **Safety Guard**: The loop is constrained by `max_handoffs` (default: 5) to prevent infinite control transfer loops between agents.

### 2.3 Intent Classification Router Pattern (`execute_router`)

1. **Fast Intent Classification**: Formulates a JSON prompt matching the query against all active agent descriptions and capabilities to select the single best agent.
2. **Direct Execution**: Bypasses decomposition overhead and executes the query directly via the chosen specialized agent.
3. **Fallback Guard**: If intent classification fails or returns an invalid slug, it gracefully defaults to the first available active candidate agent.

---

## 3. Speculative Parallel Multi-LLM Router (`LLMRouter.generate_parallel()`)

Located in `backend/app/llm/router.py`, the `LLMRouter` provides both sequential fallback generation (`generate()`) and high-performance speculative parallel LLM racing (`generate_parallel()`).

```
                    ┌───────────────────────────────┐
                    │ LLMRouter.generate_parallel() │
                    └───────────────┬───────────────┘
                                    │
           ┌──────────────┬─────────┼─────────┬──────────────┐
           ▼              ▼         ▼         ▼              ▼
     ┌───────────┐  ┌──────────┐ ┌───────┐ ┌──────────┐ ┌──────────────┐
     │ Gemini    │  │ Groq     │ │Ollama │ │ OpenAI   │ │ HuggingFace  │
     │ 1.5-Flash │  │ Llama-3.1│ │ Local │ │GPT-4o-min│ │ Llama-3.2-1B │
     └─────┬─────┘  └────┬─────┘ └───┬───┘ └────┬─────┘ └──────┬───────┘
           │             │           │          │              │
           └─────────────┴─────┬─────┴──────────┴──────────────┘
                               │ (asyncio.wait FIRST_COMPLETED)
                               ▼
                   ┌──────────────────────────┐
                   │ Fastest Non-Error Result │
                   │ (Cancel pending tasks)   │
                   └──────────────────────────┘
```

### Speculative Racing Mechanics

1. **Concurrent Execution**: `generate_parallel()` accepts a prompt and list of provider slugs (`gemini`, `groq`, `ollama`, `openai`, `huggingface`).
2. **Pre-resolution**: Provider configurations, API keys, and models are resolved sequentially beforehand to prevent concurrent DB session locking errors.
3. **`FIRST_COMPLETED` Race**: Tasks are dispatched concurrently using `asyncio.create_task()` and monitored with `asyncio.wait(..., return_when=asyncio.FIRST_COMPLETED)`.
4. **Cancellation**: As soon as the first provider returns a successful non-error response, all remaining pending tasks are immediately cancelled to save compute and API tokens.
5. **Fallback Safety**: If all parallel tasks time out or error out, the router automatically falls back to sequential fallback generation.
6. **Smart Circuit Breaker (Rate Limit Cooldown)**: If an LLM provider hits a Rate Limit (`429 RESOURCE_EXHAUSTED`), the Router intercepts the error, instantly breaks out of retry loops, and places the provider on a 60-second cooldown blocklist. Subsequent requests will immediately skip the cooled-down provider, eliminating wasted latency on fruitless retries.

---

## 4. Agent Runtime & BaseAgent ReAct Loop (`BaseAgent`)

Located in `backend/app/agents/base.py`, `BaseAgent` implements a robust ReAct (Reasoning + Acting) loop:

1. **Prompt Formatting**: Uses `app.core.toon.format_agent_context()` to format system instructions (`@sys:`), history (`@hist:`), and query (`@task:`) into compact key-value prompts.
2. **Action Parsing**:
   - `[TOOL] tool_slug | {"arg_key": "arg_value"}`: Invokes a registered tool from `ToolRegistry`.
   - `[ANSWER] {"reasoning": "...", "confidence_score": "0.95", "answer": "..."}`: Terminates loop and returns final output.
3. **Output Truncation**: `summarize_tool_result()` automatically truncates tool outputs exceeding char limits, preserving prompt efficiency while saving full raw logs to database/MinIO.

---

## 5. Modular 40-Tool Catalog Architecture

Located in `backend/app/tools/registry.py` and `backend/app/tools/modules/`, AgentHive features 40 tools split across 5 specialized sub-modules and core base tools:

| Category | Count | Tool Slugs & Names |
|---|---|---|
| **Base Infrastructure** | 13 | `file_tool`, `postgres_tool`, `redis_tool`, `minio_tool`, `loki_tool`, `code_tool` (Python Interpreter), `scraper_tool`, `translation_tool`, `youtube_transcript_tool`, `md_writer_tool`, `search_tool`, `pdf_tool`, `csv_reader_tool` |
| **Web Tools** | 9 | `wikipedia_tool`, `arxiv_tool`, `rss_reader_tool`, `url_checker_tool`, `weather_tool`, `dns_lookup_tool`, `whois_tool`, `hacker_news_tool`, `github_repo_tool` |
| **Document Tools** | 5 | `docx_tool`, `excel_writer_tool`, `pptx_tool`, `ocr_tool`, `json_yaml_tool` |
| **Text & NLP Tools** | 5 | `sentiment_tool`, `text_summarizer_tool`, `diff_tool`, `keyword_extractor_tool`, `markdown_to_html_tool` |
| **Utility Tools** | 5 | `calculator_tool`, `datetime_tool`, `image_metadata_tool`, `hash_crypto_tool`, `zip_archiver_tool` |
| **Developer Tools** | 3 | `git_tool`, `sql_query_builder_tool`, `json_schema_validator` |

---

## 6. REST API Endpoints

### 6.1 Multi-Agent Orchestration (`POST /api/orchestrate`)

- **URL**: `http://localhost:8000/api/orchestrate`
- **Request Payload**:
```json
{
  "prompt": "Analyze the latest AI research papers on ArXiv and generate a markdown summary.",
  "pattern": "supervisor",
  "target_agents": ["web_search_agent", "data_analyst"],
  "use_parallel_llm": true,
  "max_handoffs": 5
}
```
- **Response Structure**:
```json
{
  "success": true,
  "status": "completed",
  "pattern": "supervisor",
  "selected_agent": null,
  "subtasks": [
    {"agent_slug": "web_search_agent", "sub_query": "Fetch recent ArXiv papers on AI"}
  ],
  "subagent_results": [...],
  "response": "## Executive Summary of ArXiv AI Research...",
  "execution_time_seconds": 3.42,
  "details": {"num_subtasks": 1}
}
```

### 6.2 Agent Execution Endpoint (`POST /api/agents/{id}/run`)

- **URL**: `http://localhost:8000/api/agents/1/run`
- **Query Param**: `background=false` (synchronous) or `true` (enqueues Celery task)
- **Request Payload**:
```json
{
  "query": "Calculate the SHA256 hash of 'AgentHive2026'",
  "multi_agent_mode": "router",
  "use_parallel_llm": false
}
```

---

## 7. Full Observability & Infrastructure Stack

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        Observability Stack                              │
├──────────────────┬──────────────────┬──────────────────┬────────────────┤
│ Grafana Loki     │ Prometheus       │ OpenTelemetry    │ Grafana        │
│ (:3100)          │ (:9090)          │ Tracing          │ (:3001)        │
│ Log Aggregation  │ Metrics Scraping │ Trace Spans      │ Dashboards     │
└────────┬─────────┴────────┬─────────┴────────┬─────────┴────────┬───────┘
         │                  │                  │                  │
┌────────▼──────────────────▼──────────────────▼──────────────────▼───────┐
│                     AgentHive Distributed Backend                       │
│  FastAPI (:8000)  •  Celery Workers  •  PostgreSQL pgvector (:5432)     │
│  Redis (:6379)    •  MinIO S3 (:9000) •  Ollama LLM (:11434)           │
└─────────────────────────────────────────────────────────────────────────┘
```

- **PostgreSQL & pgvector (:5432)**: Persistent relational database storing agents, prompt versions, agent runs, tool calls, LLM calls, and vector memory embeddings.
- **Redis (:6379)**: Caching layer, session store, and Celery task queue broker.
- **Celery Worker**: Distributed background worker processing asynchronous agent runs.
- **MinIO Object Storage (:9000)**: S3-compatible file storage for workspace file uploads and overflow tool log storage.
- **Grafana Loki (:3100)**: Aggregates real-time application and container stdout/stderr logs.
- **Prometheus (:9090)**: Scrapes FastAPI metrics, request latencies, and LLM call duration histograms.
- **Grafana (:3001)**: Consolidated dashboards visualizing system health, agent execution timelines, and LLM provider token usage.

---

## 8. Visual Architecture Diagram

The complete interactive visual architecture diagram is saved at:
- `docs/architecture.drawio`
- `docs/diagrams/multi-agent-architecture.drawio`

Verify schema validity anytime by executing:
```bash
python docs/verify_drawio.py
```
