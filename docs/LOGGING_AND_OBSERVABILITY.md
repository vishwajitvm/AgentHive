# Logging and Observability

AgentHive must make every important action visible.

## Logging Goals

1. Debug backend APIs.
2. See what each agent is doing.
3. See why fallback happened.
4. Track token usage.
5. Track model latency.
6. Track tool usage.
7. Audit sensitive changes.
8. Find failed jobs and workflows.

## Required IDs

Every operation should carry:

```text
request_id
trace_id
user_id
agent_run_id
workflow_run_id
job_id
```

## Application Logs

Use structured logs.

Example fields:

```text
timestamp
level
service
event
request_id
user_id
agent_id
agent_run_id
workflow_run_id
provider
model
latency_ms
status
error_code
```

## Agent Step Logging

Each agent run should show timeline:

```text
1. request_received
2. agent_selected
3. memory_retrieved
4. prompt_built
5. llm_called
6. tool_called
7. fallback_used
8. response_finalized
```

## LLM Logs

Store:

- Provider.
- Model.
- Prompt ID.
- Prompt version.
- Input tokens.
- Output tokens.
- Total tokens.
- Latency.
- Error.
- Fallback reason.
- Final selected provider.

Do not store raw prompt by default if it contains sensitive user data. Store summary, hash, and sanitized preview.

## Tool Logs

Store:

- Tool name.
- Agent ID.
- Input summary.
- Output summary.
- Duration.
- Status.
- Error.

## Security Logs

Log:

- Login success/failure.
- API key added/updated/deleted.
- Agent deleted.
- Workflow changed.
- User role changed.
- Permission denied.

Never log:

- Raw API keys.
- Passwords.
- Private tokens.
- Full personal document content by default.

## Storage Split

| Data | Storage |
|---|---|
| Raw container logs | Loki |
| Metrics | Prometheus |
| Dashboards | Grafana |
| Agent run records | PostgreSQL |
| LLM usage records | PostgreSQL |
| Tool call records | PostgreSQL |
| Audit logs | PostgreSQL |

## Dashboard Filters

- Date range.
- Agent.
- Workflow.
- User.
- Model provider.
- Status.
- Fallback used.
- Error only.
- Latency range.
- Token range.
- Tool name.
- Request ID.

## Alert Examples

- Gemini quota exceeded.
- Ollama offline.
- Worker queue too large.
- PostgreSQL unavailable.
- Redis unavailable.
- Agent failure rate high.
- Token usage above threshold.
