# AgentHive Feature Specification

## 1. Dashboard

### Purpose

Central control panel for everything.

### Required Screens

- Dashboard home.
- Agent management.
- Model management.
- Tool management.
- Workflow builder.
- Logs and activity.
- Environment manager.
- File storage.
- Memory viewer.
- Monitoring.
- Settings.

### Acceptance Criteria

- User can see system health.
- User can create/edit/disable agents.
- User can change primary and fallback models.
- User can see live agent execution timeline.
- User can view logs with filters.

## 2. Agent Management

### Purpose

Create and manage agent bots.

### Fields

- Agent name.
- Agent type.
- Agent description.
- System prompt.
- Prompt version.
- Allowed tools.
- Primary model override.
- Fallback policy override.
- Max steps.
- Timeout.
- Memory enabled/disabled.
- Status.

### Required Agents for MVP

1. Personal Assistant Agent.
2. Task Agent.
3. PDF Agent.
4. Research Agent.
5. Developer Agent.
6. Reminder Agent.

### Acceptance Criteria

- Agent configs stored in database.
- No agent model is hardcoded.
- Every agent run creates logs.
- Agent version history is preserved.

## 3. Model Management

### Purpose

Control Gemini, Ollama, Hugging Face, GPT, and other providers from dashboard.

### Fields

- Provider name.
- Provider type.
- Base URL.
- API key reference.
- Default model.
- Context size.
- Max output tokens.
- Timeout.
- Rate limit.
- Health status.
- Enabled/disabled.

### Acceptance Criteria

- Gemini can be default primary.
- Ollama can be default fallback.
- User can reorder fallback providers.
- Router respects dashboard settings.

## 4. LLM Router

### Purpose

One common entrypoint for all model calls.

### Responsibilities

- Select provider.
- Count/estimate tokens.
- Compress context.
- Apply fallback.
- Normalize responses.
- Log usage.

### Acceptance Criteria

- Provider failure does not crash the whole request.
- Fallback reason is visible.
- Token usage is stored.

## 5. Workflow Builder

### Purpose

Let users connect agents together.

Example:

```text
PDF upload -> PDF Agent -> Task Agent -> Reminder Agent
```

### Features

- Node-based workflow definition.
- Trigger conditions.
- Retry policy.
- Manual approval step.
- Dead-letter failed runs.
- Run history.

### Acceptance Criteria

- Circular workflows blocked.
- Workflow versions are stored.
- Running workflows use config snapshot.

## 6. Tool Management

### Purpose

Control what agents are allowed to do.

### Tools

- File Tool.
- PDF Tool.
- Search Tool.
- Storage Tool.
- Code Tool.
- Email Tool later.
- Calendar Tool later.
- GitHub Tool later.

### Acceptance Criteria

- Tools can be enabled/disabled per agent.
- Tool calls are logged.
- Tool output summaries are token-limited.

## 7. Logging and Live Activity

### Purpose

Show exactly what the bot is doing.

### Required Views

- Live activity feed.
- Agent run timeline.
- LLM call logs.
- Tool call logs.
- Workflow logs.
- Error logs.
- Security audit logs.

### Acceptance Criteria

- Every request has request_id.
- Every agent run has agent_run_id.
- Every workflow run has workflow_run_id.
- Logs are searchable and filterable.

## 8. Environment Manager

### Purpose

Set provider keys and URLs one time from dashboard.

### Important

Secrets must be encrypted. Raw secrets must not be logged.

### Acceptance Criteria

- User can save Gemini API key.
- User can save Hugging Face key.
- User can configure Ollama URL.
- Secret changes are audited.
