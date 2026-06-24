# MinIO Storage Tool

## Overview
**Category:** core
**Description:** Uploads/downloads files from object storage.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY

### Input Schema
```json
{
  "action": "string",
  "object_name": "string",
  "content": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
