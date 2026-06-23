# File System Tool

## Overview
**Category:** core
**Description:** Reads, writes, lists local project files safely.

## Schema Details
- **Safe Mock Mode:** False
- **Requires Auth:** False
- **Required Env Keys:** None

### Input Schema
```json
{
  "action": "string",
  "filename": "string",
  "content": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
