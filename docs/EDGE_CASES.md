# Edge Cases and Handling Plan

## LLM Provider Edge Cases

| Edge Case | Handling |
|---|---|
| Gemini quota exceeded | Fallback to Ollama, log fallback reason |
| Gemini token limit exceeded | Compress context, retry once, fallback if still too large |
| Gemini invalid API key | Mark provider unhealthy, alert dashboard |
| Ollama offline | Skip Ollama fallback, try next provider |
| Ollama model not downloaded | Show dashboard action to pull model |
| Hugging Face rate limited | Retry with backoff, fallback |
| GPT disabled | Router must not call GPT |
| Provider returns empty output | Retry once, fallback |
| Provider returns invalid format | Response normalizer attempts repair, then fallback |

## Token Edge Cases

| Edge Case | Handling |
|---|---|
| Large PDF | Chunk document and summarize chunks |
| Long chat history | Summarize history and keep recent turns |
| Huge tool output | Store full output in file/storage, pass summary to LLM |
| Memory too large | Top-k retrieval and relevance threshold |
| JSON too large | Convert to TOON or compact key-value |

## Agent Edge Cases

| Edge Case | Handling |
|---|---|
| Infinite loop | max_steps and timeout |
| Wrong tool selected | tool allowlist and tool schema validation |
| Agent calls too many tools | per-run tool limit |
| Agent fails mid-run | save failed step and allow retry/resume |
| Agent deleted during run | active run uses config snapshot |
| Prompt changed during run | active run uses prompt version snapshot |

## Workflow Edge Cases

| Edge Case | Handling |
|---|---|
| Circular workflow | DAG validation before publish |
| Node missing | workflow validation error |
| Retry loop | retry limit and dead-letter queue |
| Duplicate execution | idempotency key |
| Workflow edited during run | run uses published version snapshot |
| Manual approval timeout | mark waiting/expired based on policy |

## Docker Edge Cases

| Edge Case | Handling |
|---|---|
| Backend crash | restart policy, logs, health check |
| Worker crash | restart policy, job retry |
| Redis unavailable | readiness check fails |
| Postgres unavailable | API returns controlled error |
| MinIO unavailable | file operations fail gracefully |
| Disk full | retention policies and alerts |
| Port conflict | documented port mapping |

## Security Edge Cases

| Edge Case | Handling |
|---|---|
| Secret logged accidentally | masking utility and logger filter |
| User changes provider key | audit log event |
| Unauthorized tool access | permission check before tool call |
| Prompt injection in document | tool permission boundaries and instruction hierarchy |
| Malicious file upload | file type and size validation |

## Dashboard Edge Cases

| Edge Case | Handling |
|---|---|
| Empty fallback order | validation prevents save |
| Invalid API key | health check marks provider unhealthy |
| User selects unavailable model | validation shows error |
| Logs too large | pagination and retention |
| Metrics service down | dashboard shows degraded state |
