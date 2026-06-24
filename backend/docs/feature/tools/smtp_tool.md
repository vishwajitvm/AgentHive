# Email SMTP Tool

## Overview
**Category:** communication
**Description:** Sends emails through configured SMTP.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS

### Input Schema
```json
{
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
