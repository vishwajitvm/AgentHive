# Deep Developer Trace Integration

The user requested a highly detailed, developer-centric flow that includes internal architectural steps (like LLM routing, memory/vector hits, model failovers, and latency) interleaved directly into the step-by-step flowchart.

## Proposed Changes

### 1. Unified Chronological Timeline (Frontend)
- **[MODIFY] [logs/page.tsx](file:///c:/python/AgentHive/frontend/src/app/logs/page.tsx)**: 
  - Update `openTraceModal` to fetch `getLlmCalls(run.id)` alongside `getRunSteps`.
  - Merge the standard `AgentSteps` (thoughts, tools) with the internal `LLMCalls` (model routing, failures).
  - Sort the combined array chronologically by `created_at` to create a single true timeline.
- **[MODIFY] [agents/[id]/page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/%5Bid%5D/page.tsx)**:
  - Do the same merging logic for live executions so the diagram updates in real-time with LLM routing blocks.

### 2. Enhanced Diagram Visuals
- **[MODIFY] [TraceDiagram.tsx](file:///c:/python/AgentHive/frontend/src/components/TraceDiagram.tsx)**:
  - Add visual rendering logic for new internal step types:
    - `llm_call`: Displays the model provider, latency, tokens used. If the LLM call failed and triggered a fallback, it will render as a red/amber alert node displaying the exact `fallback_reason` and error message.
    - Add custom icons (`Cpu`, `Zap`, `ServerCrash`) for these infrastructure-level steps.
    - Format the JSON payload beautifully.

## Verification Plan
1. Open the Trace Modal on an existing run.
2. Verify that LLM routing steps (showing Model X, X ms latency, success/fail) are interleaved exactly where they happened between thoughts and tool calls.
