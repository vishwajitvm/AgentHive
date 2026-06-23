# WhatsApp Business Tool

## Overview
**Category:** social
**Description:** Architecture for WhatsApp Business Cloud API. Use mock mode if credentials are missing.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** True
- **Required Env Keys:** WHATSAPP_API_TOKEN, WHATSAPP_PHONE_NUMBER_ID

### Input Schema
```json
{
  "to_number": "string",
  "message": "string"
}
```

### Output Schema
```json
{
  "result": "string"
}
```
