# Redis Cache Tool

## Overview
**Category:** database
**Description:** Reads/writes temporary cached values.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** REDIS_URL

### Input Schema
```json
{
  "action": "string",
  "key": "string",
  "value": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
