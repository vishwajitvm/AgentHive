# Master Implementation Plan for AgentHive V2

This plan outlines the approach to fully fix the existing AgentHive framework and expand it with the 20+ requested agents, 20+ requested tools, UI updates, and comprehensive MD/DOCX documentation.

## User Review Required

> [!WARNING]
> This is a massive feature roadmap. I will proceed through these phases methodically to ensure nothing breaks.
> Do you approve this roadmap structure? Any final changes to the agent/tool list before I begin implementation?

## Proposed Changes

We will execute this according to the 14 phases provided:

### Phase 1 & 2: Project Audit & Fix Existing Agents
- **Audit**: We've confirmed frontend, backend, database, celery workers, and LLM routes (Gemini & Ollama) are generally healthy. We will patch any remaining broken routes or imports.
- **Verification**: Ensure the 5 current agents (Developer, PDF, PA, Research, Task Checklist) work perfectly.
- **Database Extension**: Add a `Tool` SQLAlchemy model in `backend/app/tools/models.py` to support dynamic tool CRUD with fields: `slug, name, description, category, input_schema, output_schema, is_enabled, requires_auth, required_env_keys, safe_mock_mode`.

### Phase 3: Add 20+ Advanced Tools
- **New Tool Models**: Implement tool classes following the `BaseTool` pattern.
- **Mock Modes**: Ensure external API tools (WhatsApp, Instagram, Gmail, GitHub, etc.) have `safe_mock_mode` logic.
- **List of Tools**:
  1. File System, 2. PDF Text Extractor, 3. Web Search, 4. Code Interpreter, 5. MinIO Storage, 6. PostgreSQL Query, 7. Redis Cache, 8. Email SMTP, 9. Gmail, 10. Google Calendar, 11. GitHub, 12. Markdown Writer, 13. DOCX Writer, 14. CSV/Excel Reader, 15. Website Scraper, 16. Notification, 17. WhatsApp Business, 18. Instagram Business, 19. Image Analysis, 20. OCR, 21. API Request, 22. Document Summarizer, 23. Embedding, 24. Vector Search, 25. Log Search.

### Phase 4: Add 20+ Advanced Agents
- **Registration**: Add them to the database seeding script or create them via API.
- **Agent Prompts**: Define clear `system_prompt` instructions and tool bindings for each.
- **List of Agents**:
  WhatsApp Assistant, Instagram Content, Social Media Manager, Email Assistant, Calendar Scheduler, Meeting Notes, Invoice Assistant, Expense Tracker, Customer Support, Sales Lead, CRM Assistant, Blog Writer, SEO Research, Resume Builder, Study Planner, Fitness Planner, Diet Planner, Travel Planner, Shopping Research, Legal Document Helper, HR Policy, Data Analyst, Report Generator, Bug Triage, Deployment Helper.

### Phase 5 & 12: Frontend Updates
- **Agent Registry Page**: Display all new attributes (Status, Tool tags, Default Model).
- **Create/Edit Agent Page**: Expand form fields.
- **New Tools Page** (`/tools`): Display all 20+ tools with schemas and mock status.
- **Logs Page**: Show execution trails and router fallbacks.
- **Agent Run Dashboard**: Live step logs, fallback info, tool usage, token consumption.

### Phase 6, 7, 8, 9: Comprehensive Documentation
- **Folder Structure**: `docs/feature/agents/` and `docs/feature/tools/`
- **MD & DOCX Files**: Generate both `.md` (dev-focused) and `.docx` (layman-focused) files for all 45+ agents/tools.
- **Master Feature Guide**: Create a central directory guide.
- **Demo Requirements**: 3 workflow examples embedded in each agent's `.docx`.

### Phase 10 & 11: Backend & Edge Cases
- **Strict Backend Order**: Imports -> Health -> Database -> Tool Models -> Agent Models -> Tool/Agent CRUD APIs -> Implement 25 Tools -> Implement 25 Agents -> Expand Error Catching.
- **Edge Cases**: 500 errors, rate limits, missing API keys, and invalid outputs will be gracefully caught by the `orchestrator` and sent to the frontend logs without crashing the Next.js app.

## Verification Plan

### Automated/Manual Testing
- Boot up full Docker stack (`docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`).
- Run the 5 legacy agents to confirm no regressions.
- Execute the CRUD tool API endpoint to verify 25 tools populate.
- Navigate to the frontend `/tools` and `/agents` pages to ensure UI components don't crash.
- Run a multi-step Workflow (e.g. WhatsApp Agent using WhatsApp Mock Tool + Document Summarizer Tool) to verify deep end-to-end integration.
- Ensure all `.md` and `.docx` files are valid and readable.
