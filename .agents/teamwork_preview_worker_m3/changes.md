# Changes Log — Milestone 3 (M3): Specialized Agent Portfolio Expansion & Database Seeding

## Summary of Changes

### 1. `backend/app/agents/seeder.py`
- Defined `SPECIALIZED_AGENTS`, a portfolio of 30 distinct, specialized agent configurations with rich prompts, max steps, timeouts, and tool mapping.
- Ensured explicit definitions for all key specialized roles required by M3:
  - `general_assistant` (`file_tool`, `md_writer_tool`, `markdown_to_html_tool`, `text_summarizer_tool`)
  - `web_search_agent` (`search_tool`, `wikipedia_tool`, `arxiv_tool`, `hacker_news_tool`, `github_repo_tool`, `weather_tool`, `url_checker_tool`)
  - `data_analyst` (`csv_reader_tool`, `excel_writer_tool`, `json_yaml_tool`, `calculator_tool`, `sentiment_tool`)
  - `fact_checker_agent` (`search_tool`, `wikipedia_tool`, `diff_tool`, `keyword_extractor_tool`, `whois_tool`)
  - `fullstack_dev` & `code_architect` (`code_tool`, `git_tool`, `json_schema_validator`, `sql_query_builder_tool`, `diff_tool`)
  - `system_debugger` (`loki_tool`, `redis_tool`, `postgres_tool`, `url_checker_tool`, `dns_lookup_tool`)
  - `doc_processor` (`pdf_tool`, `docx_tool`, `excel_writer_tool`, `pptx_tool`, `ocr_tool`, `md_writer_tool`)
- Added `upsert_specialized_agents(db: AsyncSession)` to handle both insertion of new agents and updating of existing agents along with their associated `Prompt` and `PromptVersion` records on startup.
- Updated `initialize_agents(db)` and `seed_new_agents(db)` to call `upsert_specialized_agents(db)`.

### 2. `backend/app/agents/registry.py`
- Re-exported `initialize_agents` and `DEFAULT_AGENTS` from `app.agents.seeder` to ensure startup pre-population and application initialization stay synchronized.

### 3. `backend/seed_elite_agents.py`
- Updated agent seeding dataset to utilize `SPECIALIZED_AGENTS` from `app.agents.seeder`.
- Cleaned up database wipe and seed routine to create and link `Agent`, `Prompt`, and `PromptVersion` records cleanly.

### 4. `backend/seed_50_agents.py`
- Expanded agent portfolio to 50 specialized agents (combining the 30 primary specialized agents with 20 additional specialized agent configurations).
- Mapped all 50 agents exclusively to valid registered tool slugs in `ToolRegistry` (eliminating outdated tool references like `storage_tool` in favor of `minio_tool`).

### 5. `backend/test_m3_agents.py` (New File)
- Implemented comprehensive M3 verification test suite:
  - `test_tool_registry_mapping()`: Verifies all 40 registered tools in `ToolRegistry`.
  - `test_specialized_agents_config()`: Verifies that at least 25+ specialized agents exist, all mandatory roles are present, and every tool slug maps to a valid tool in `ToolRegistry`.
  - `test_database_seeding_and_upsert()`: Simulates async database seeding and upserting via `MockAsyncSession` to verify DB/memory model creation and updating.

## Verification Commands & Results

```powershell
# 1. Run M3 Specialized Agents Test Suite
python test_m3_agents.py
# Output:
# [TEST 1] Registered Tools in ToolRegistry: 40
# [TEST 2] Specialized Agents portfolio count: 30
# [TEST 2] All mandatory specialized agent roles present: {'general_assistant', 'fact_checker_agent', 'system_debugger', 'doc_processor', 'web_search_agent', 'data_analyst', 'code_architect', 'fullstack_dev'}
# [TEST 2] All tool slug mappings across all 50 agents belong to valid ToolRegistry tools.
# [TEST 3] Database seeding & upsert verified successfully! Total agents seeded/upserted: 30
# ALL M3 AGENT VERIFICATION TESTS PASSED!

# 2. Run Existing Test Suite
python -m pytest tests/
# Output: 6 passed in 4.03s
```
