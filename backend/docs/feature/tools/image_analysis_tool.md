# Image Analysis Tool

## Overview
**Category:** vision
**Description:** Extracts metadata or analyzes uploaded images using selected model.

## Schema Details
- **Safe Mock Mode:** True
- **Requires Auth:** False
- **Required Env Keys:** None

### Input Schema
```json
{
  "image_url_or_path": "string"
}
```

### Output Schema
```json
{
  "analysis": "string"
}
```
