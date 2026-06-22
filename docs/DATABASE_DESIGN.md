# Database Design

## Primary Database

Use PostgreSQL.

## Vector Extension

Enable pgvector for memory and document embeddings.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

## Core Tables

### users

Stores application users.

Fields:

- id
- email
- name
- role
- status
- created_at
- updated_at

### agents

Stores agent configuration.

Fields:

- id
- name
- slug
- description
- agent_type
- prompt_id
- model_policy_id
- tools_enabled
- memory_enabled
- max_steps
- timeout_seconds
- status
- created_at
- updated_at

### agent_versions

Stores versioned agent configuration snapshots.

### model_providers

Stores provider settings.

Fields:

- id
- provider_name
- provider_type
- base_url
- api_key_secret_id
- default_model
- enabled
- health_status
- created_at
- updated_at

### model_policies

Stores primary and fallback rules.

Fields:

- id
- name
- primary_provider
- secondary_provider
- fallback_order
- max_input_tokens
- max_output_tokens
- timeout_seconds
- retry_count

### prompts

Stores prompt templates.

### prompt_versions

Stores prompt version history.

### workflows

Stores workflow definitions.

### workflow_runs

Stores workflow execution records.

### workflow_steps

Stores each workflow node execution.

### agent_runs

Stores each agent execution.

### agent_steps

Stores each agent step.

### llm_calls

Stores each LLM call summary.

### tool_calls

Stores each tool execution summary.

### files

Stores MinIO file metadata.

### memories

Stores vector memory.

Fields:

- id
- owner_type
- owner_id
- content_summary
- content_hash
- embedding vector
- metadata
- created_at

### secrets

Stores encrypted secret references.

### audit_logs

Stores security and configuration changes.

## Important Indexes

- users.email unique.
- agents.slug unique.
- agent_runs.agent_id.
- agent_runs.user_id.
- agent_steps.agent_run_id.
- llm_calls.agent_run_id.
- workflow_runs.workflow_id.
- memories vector index.
- audit_logs.created_at.

## Versioning Rule

When an agent, prompt, workflow, or model policy changes, create a new version row. Active runs should use a snapshot so changes do not break running jobs.
