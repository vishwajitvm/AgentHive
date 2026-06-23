# Invoice Assistant Agent

## Overview
**Type:** finance
**Description:** Reads invoices and extracts key data.

## Configuration
- **Max Steps:** 5
- **Timeout:** 60s
- **Memory Enabled:** True
- **Tools Permitted:** pdf_tool, ocr_tool, csv_reader_tool

## Technical Architecture
The agent is orchestrated using the `base.py` execution loop. It binds dynamically to the specified tool profiles and enforces maximum iteration caps to prevent infinite loops.

## Demos

### Demo 1: Basic Inquiry
**User:** Can you help me with a basic task?
**Agent:** Yes, I can assist you based on my configured tools.

### Demo 2: Tool Execution
**User:** Use your tool to retrieve data.
**Agent:** Accessing tool... Data retrieved successfully.

### Demo 3: Edge Case
**User:** Do something outside your scope.
**Agent:** I apologize, but I am not authorized to perform that action.
