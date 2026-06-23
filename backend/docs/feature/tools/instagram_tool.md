# Instagram Business Tool

## Overview
**Category:** social
**Description:** Architecture for Instagram Graph API. Use mock mode if credentials are missing.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** INSTAGRAM_ACCESS_TOKEN, INSTAGRAM_ACCOUNT_ID

### Input Schema
```json
{
  "action": "string",
  "media_url": "string",
  "caption": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
