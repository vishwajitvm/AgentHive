# GitHub Tool

## Overview
**Category:** development
**Description:** Reads repos, issues, PRs, and commits.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** GITHUB_TOKEN

### Input Schema
```json
{
  "action": "string",
  "repo": "string",
  "issue_title": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
