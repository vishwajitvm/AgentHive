# Google Calendar Tool

## Overview
**Category:** communication
**Description:** Creates/reads calendar events through official OAuth architecture or mock mode.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** GCAL_OAUTH_TOKEN

### Input Schema
```json
{
  "action": "string",
  "summary": "string",
  "start_time": "string",
  "end_time": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
