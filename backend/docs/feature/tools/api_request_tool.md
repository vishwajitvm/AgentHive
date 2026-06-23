# API Request Tool

## Overview
**Category:** web
**Description:** Allows controlled HTTP calls to approved domains only.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** False
- **Required Env Keys:** None

### Input Schema
```json
{
  "method": "string",
  "url": "string",
  "headers": "dict",
  "body": "dict"
}
```

### Output Schema
```json
{
  "response": "string"
}
```
