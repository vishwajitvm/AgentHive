# Versioning Policy

## Versioned Items

AgentHive must version:

- Agents.
- Prompts.
- Workflows.
- Model policies.
- Tool configurations.
- Documentation.

## Version Format

Use semantic versioning for releases:

```text
MAJOR.MINOR.PATCH
```

Example:

```text
0.1.0
```

## Agent Versioning

When agent prompt, tools, model policy, memory setting, or max steps change, create new agent version.

## Workflow Versioning

Draft workflows can be edited freely. Published workflows must create a new version when changed.

## Documentation Versioning

Whenever code changes, update matching docs. If docs are not updated, the feature is not complete.

## Changelog Rule

Every meaningful change must be added to `CHANGELOG.md`.
