# Gmail Tool

## Overview
**Category:** communication
**Description:** Reads/sends Gmail through official OAuth architecture or mock mode.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** GMAIL_OAUTH_TOKEN

### Input Schema
```json
{
  "action": "string",
  "to": "string",
  "subject": "string",
  "body": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
