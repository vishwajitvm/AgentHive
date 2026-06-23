# PostgreSQL Query Tool

## Overview
**Category:** database
**Description:** Runs safe internal queries only.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** DATABASE_URL

### Input Schema
```json
{
  "query": "string"
}
```

### Output Schema
```json
{
  "results": "array"
}
```
