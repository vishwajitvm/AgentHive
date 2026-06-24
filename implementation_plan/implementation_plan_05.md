# Comprehensive Developer Data View

The user requested an absolute "God Mode" developer view where they can see the raw underlying database payloads, relationships, and unformatted logs for debugging purposes. They want a third tab in the trace modal.

## Proposed Changes

### 1. New "Raw Developer Data" Tab
- **[MODIFY] [logs/page.tsx](file:///c:/python/AgentHive/frontend/src/app/logs/page.tsx)**:
  - Add a third toggle button: **"Layman Summary" | "Technical Trace" | "Raw DB / Developer"**.
  - When the Developer tab is selected, it will render a comprehensive, collapsible raw JSON dump of:
    1. **AgentRun Object**: The raw database record for the execution.
    2. **Agent Config**: The raw configuration of the agent that executed it.
    3. **Unified Steps (with LLM & Memory traces)**: The exact JSON payload sent from the backend API.
    4. **Raw Tool Calls**: The raw tool execution database table records.
  - This provides 100% visibility into the data structures and relationships exactly as they exist in Postgres.

### 2. UI Visibility Fixes
- The user mentioned "things are not showing on ui level for now". I will investigate if any old runs (like Run #5) are missing fields (e.g. `metadata`) that caused the UI to silently hide them. The raw JSON view will immediately make it obvious if the database is missing data for older runs.

## Verification Plan
1. Open the Trace Modal.
2. Click the new `Database` icon tab for Developer Data.
3. Verify that the raw JSON objects are fully visible and perfectly reflect the backend database state.
