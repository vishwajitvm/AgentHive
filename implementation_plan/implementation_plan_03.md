# Agent Console Context Enhancement

This plan addresses the UI crash (`CheckCircle` missing) and introduces the requested capabilities for supplying files and credentials to agents.

## Proposed Changes

### 1. Fix Frontend Runtime Error
- **[MODIFY] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/%5Bid%5D/page.tsx)**: Add `CheckCircle` to the `lucide-react` imports to resolve the frontend rendering crash.

### 2. Backend Workspace Upload API
- **[MODIFY] [agents.py](file:///c:/python/AgentHive/backend/app/api/routes/agents.py)**: Add a `POST /workspace/upload` endpoint using FastAPI's `UploadFile`. This will save documents (PDFs, text files) directly to the Agent's local `WORKSPACE_DIR` so that the `file_tool` and `pdf_tool` can read them.

### 3. Frontend Context UI
- **[MODIFY] [api.ts](file:///c:/python/AgentHive/frontend/src/lib/api.ts)**: Add `uploadToWorkspace` API call function.
- **[MODIFY] [page.tsx](file:///c:/python/AgentHive/frontend/src/app/agents/%5Bid%5D/page.tsx)**: 
  - Add a **"Workspace Upload"** button allowing users to upload PDFs and documents directly into the active workspace before running the agent.
  - Add a **"Session Context Variables"** panel. Users can securely paste social media credentials or additional context here without hardcoding it in the `.env` file, and it will be seamlessly prepended to their prompt when executing the agent.

### 4. Update Documentation and Diagrams
- **[MODIFY] [FEATURE_SPECIFICATION.md](file:///c:/python/AgentHive/docs/FEATURE_SPECIFICATION.md)**: Add documentation for the new Session Context and Workspace File features.
- **[MODIFY] [request-data-flow.drawio](file:///c:/python/AgentHive/docs/diagrams/request-data-flow.drawio)**: Inject a new architectural block in the data flow representing "Inject Workspace/Session Context".

## Verification Plan
1. Upload a sample document via the UI and verify it saves to the backend workspace successfully.
2. Provide a mock credential in the "Session Context Variables" input and run a prompt. Verify the prompt executed correctly without a `CheckCircle` error.
