# AgentHive Feature Specification & Capability Matrix

> **Official Feature Specification detailing Multi-Agent Orchestration, Speculative LLM Racing, Categorized 40-Tool Catalog, REST APIs, and System Verification Instructions.**

---

## 1. Dashboard & Management UI

### Purpose
Centralized web console for monitoring, configuring, and executing AI agents, model policies, tool permissions, and workflows.

### Key Capabilities
- **System Health & Observability**: Real-time service status indicators for PostgreSQL, Redis, Celery, MinIO, Loki, and Prometheus.
- **Agent Lifecycle Management**: CRUD operations for agents, prompt versioning, tool entitlement toggles, memory settings, max step limits, and timeouts.
- **Model Policy & Fallback Engine**: Reorder fallback chains across Gemini, Groq, Ollama, OpenAI, and HuggingFace.
- **Agent Run Timeline & Log Viewer**: Live step-by-step audit feed of agent thoughts, tool calls, observations, and LLM call latencies.

---

## 2. Multi-Agent Orchestration Engine (`MultiAgentEngine`)

### Purpose
Orchestrates multi-agent execution across complex user queries using Supervisor, Swarm, Router, or Automated classification strategies.

### Multi-Agent Modes
1. **Supervisor Mode (`supervisor`)**:
   - Analyzes complex multi-step user prompts.
   - Decomposes request into sub-tasks assigned to specialized agent slugs.
   - Dispatches sub-tasks to agents in sequence.
   - Synthesizes all sub-task outputs into a cohesive final answer.
2. **Swarm Mode (`swarm`)**:
   - Executes dynamic peer-to-peer agent control transfers.
   - Parses `[HANDOFF] target_slug | {"context": "..."}` tags in agent output.
   - Continues peer handoff loop up to `max_handoffs` limit.
3. **Router Mode (`router`)**:
   - Performs fast intent classification using LLM prompt.
   - Selects the single best specialized candidate agent and dispatches query directly.
4. **Auto Mode (`auto`)**:
   - Classifies prompt into `supervisor`, `swarm`, or `router` automatically before execution.

---

## 3. Speculative Parallel LLM Racing (`LLMRouter.generate_parallel()`)

### Purpose
Eliminates LLM inference bottlenecks by querying multiple providers concurrently and returning the fastest non-error result.

### Key Features
- **Concurrent Provider Racing**: Dispatches prompt simultaneously to configured providers (Gemini 1.5 Flash, Groq Llama3, Ollama Local, OpenAI GPT-4o-mini, HuggingFace Llama 3.2).
- **First-Completed Strategy**: Uses `asyncio.wait(..., return_when=FIRST_COMPLETED)` to capture the winner response immediately and cancel pending slower calls.
- **Pre-resolved API Keys**: Resolves provider keys sequentially beforehand to ensure thread-safe async database sessions.
- **Automatic Fallback**: Reverts to sequential provider chain if all parallel providers fail or time out.

---

## 4. Modular 40-Tool Catalog & 5 Category Sub-modules

### Purpose
Empowers specialized agents with sandboxed capabilities spanning web search, document processing, text analysis, utilities, and developer tooling.

### Tool Inventory (40 Total Tools)

#### 4.1 Base Infrastructure Tools (13 Tools)
- `file_tool`: Reads, writes, or lists files in local workspace directory.
- `postgres_tool`: Executes read-only SQL queries against internal PostgreSQL database.
- `redis_tool`: Interacts with Redis cache (GET/SET/KEYS).
- `minio_tool`: Uploads and downloads files from MinIO object storage.
- `loki_tool`: Queries Loki log server via LogQL.
- `code_tool`: Sandboxed Python interpreter (`exec` with restricted builtins).
- `scraper_tool`: Extracts clean readable text from HTML web pages.
- `translation_tool`: Translates foreign text to English via Google Translate API.
- `youtube_transcript_tool`: Fetches video transcripts from YouTube URLs.
- `md_writer_tool`: Writes structured markdown report files.
- `search_tool`: Queries DuckDuckGo web search snippets.
- `pdf_tool`: Reads text content from PDF documents.
- `csv_reader_tool`: Reads CSV or Excel files into markdown tables.

#### 4.2 Web Tools Sub-module (`app/tools/modules/web_tools.py` - 9 Tools)
- `wikipedia_tool`: Queries Wikipedia summaries and page links.
- `arxiv_tool`: Searches ArXiv scientific research papers.
- `rss_reader_tool`: Parses RSS/Atom news feeds.
- `url_checker_tool`: Performs HTTP status and header health checks.
- `weather_tool`: Fetches current weather and forecasts for locations.
- `dns_lookup_tool`: Queries DNS A, MX, TXT, and NS records.
- `whois_tool`: Looks up domain registration details.
- `hacker_news_tool`: Fetches top trending stories from Hacker News.
- `github_repo_tool`: Inspects GitHub repository details, stars, and open issues.

#### 4.3 Document Tools Sub-module (`app/tools/modules/doc_tools.py` - 5 Tools)
- `docx_tool`: Reads and writes Microsoft Word `.docx` documents.
- `excel_writer_tool`: Creates formatted Excel workbooks from tabular data.
- `pptx_tool`: Generates PowerPoint presentations.
- `ocr_tool`: Extracts text from images using OCR.
- `json_yaml_tool`: Validates and converts between JSON and YAML formats.

#### 4.4 Text & NLP Tools Sub-module (`app/tools/modules/text_tools.py` - 5 Tools)
- `sentiment_tool`: Analyzes sentiment polarity and subjectivity.
- `text_summarizer_tool`: Summarizes long text into key takeaways.
- `diff_tool`: Generates line-by-line diff comparisons between two texts.
- `keyword_extractor_tool`: Extracts key phrases and topic tags.
- `markdown_to_html_tool`: Converts markdown markup to clean HTML.

#### 4.5 Utility Tools Sub-module (`app/tools/modules/utility_tools.py` - 5 Tools)
- `calculator_tool`: Evaluates mathematical expressions safely.
- `datetime_tool`: Handles timezone conversions and date math.
- `image_metadata_tool`: Extracts EXIF metadata and image dimensions.
- `hash_crypto_tool`: Generates SHA256, MD5, and HMAC hashes.
- `zip_archiver_tool`: Creates and extracts ZIP file archives.

#### 4.6 Developer Tools Sub-module (`app/tools/modules/dev_tools.py` - 3 Tools)
- `git_tool`: Executes Git commands (status, log, diff, commit).
- `sql_query_builder_tool`: Builds SQL queries dynamically.
- `json_schema_validator`: Validates JSON payloads against JSON Schema definitions.

---

## 5. REST API Endpoints

| Endpoint | Method | Description | Payload Schema |
|---|---|---|---|
| `/api/orchestrate` | POST | Executes multi-agent dynamic orchestration across Supervisor, Swarm, or Router patterns | `MultiAgentRequest` |
| `/api/agents/{id}/run` | POST | Executes an agent directly or delegates to MultiAgentEngine | `RunPayload` |
| `/api/agents` | GET | Lists all active agents and configurations | None |
| `/api/agents/runs/{run_id}/steps` | GET | Retrieves step-by-step execution timeline, tool calls, and LLM calls | None |
| `/api/agents/workspace/upload` | POST | Uploads document to workspace directory for agent analysis | `Multipart File` |

---

## 6. Verification Instructions

### 6.1 Draw.io Architecture Diagram Verification
To verify XML schema validity for `docs/architecture.drawio` and `docs/diagrams/multi-agent-architecture.drawio`:
```bash
python docs/verify_drawio.py
```

### 6.2 Pytest Unit & Integration Test Verification
To execute the automated test suite verifying multi-agent engine, LLM router, and tool registry:
```bash
pytest backend/tests/ -v
```
