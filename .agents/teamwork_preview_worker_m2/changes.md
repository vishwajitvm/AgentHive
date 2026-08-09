# M2 Changes Log — Massive Tool Expansion

**Author**: teamwork_preview_worker_m2  
**Date**: 2026-08-09  
**Milestone**: M2 (Massive Tool Expansion - 27+ New Tools across 5 Categories)  

---

## 1. Summary of Changes

Milestone 2 expands AgentHive's tool ecosystem from 13 core tools to **40 comprehensive zero-cost and local Python tools** across 5 distinct domain categories: **Web**, **Document**, **Text**, **Utility**, and **Developer**.

All tools inherit from `BaseTool`, implement asynchronous `run(**kwargs) -> str` execution, and handle error edge-cases and API fallbacks gracefully without crashing.

---

## 2. Detailed File Modifications

### 2.1 Created Modular Tool Package (`backend/app/tools/modules/`)
Created directory `backend/app/tools/modules/` containing 5 category files and `__init__.py`:

1. **`backend/app/tools/modules/__init__.py`**:
   - Package initialization for tool category modules.

2. **`backend/app/tools/modules/web_tools.py`** (9 Web Tools):
   - `wikipedia_tool` (`WikipediaTool`): Searches Wikipedia articles, fetches desktop page URLs and extracts summaries. Fallback to MediaWiki search API.
   - `arxiv_tool` (`ArxivTool`): Queries scientific preprints via ArXiv XML API, extracting titles, authors, publication dates, and abstracts.
   - `rss_reader_tool` (`RssReaderTool`): Parses RSS/Atom feeds using `feedparser` with `httpx` XML fallback.
   - `url_checker_tool` (`UrlCheckerTool`): Audits HTTP status, redirect chains, server info, and response headers via `httpx`.
   - `weather_tool` (`WeatherTool`): Geocodes city names and fetches live weather forecasts via free Open-Meteo REST API.
   - `dns_lookup_tool` (`DnsLookupTool`): Resolves DNS records (A, AAAA, MX, TXT, CNAME, NS) via `dnspython` with `socket` fallback.
   - `whois_tool` (`WhoisTool`): Parses domain WHOIS info (registrar, creation/expiration dates, name servers) via `whois` or RDAP endpoint.
   - `hacker_news_tool` (`HackerNewsTool`): Queries HackerNews Firebase REST API for top, new, or best tech stories and comments.
   - `github_repo_tool` (`GithubRepoTool`): Inspects GitHub repositories, commit logs, open issues, and releases via GitHub REST API.

3. **`backend/app/tools/modules/doc_tools.py`** (5 Document Tools):
   - `docx_tool` (`DocxTool`): Reads, creates, and appends to Microsoft Word `.docx` documents using `python-docx`.
   - `excel_writer_tool` (`ExcelWriterTool`): Builds multi-sheet Excel spreadsheets (`.xlsx`) from JSON data or CSV strings using `pandas` and `openpyxl`.
   - `pptx_tool` (`PptxTool`): Extracts text from slides or generates formatted PowerPoint presentations (`.pptx`) using `python-pptx`.
   - `ocr_tool` (`OcrTool`): Extracts text from workspace images using `Pillow` and `pytesseract` with graceful fallback info when Tesseract OCR binary is absent.
   - `json_yaml_tool` (`JsonYamlTool`): Validates, formats, and converts between JSON and YAML using `json` and `pyyaml`.

4. **`backend/app/tools/modules/text_tools.py`** (5 Text & NLP Tools):
   - `sentiment_tool` (`SentimentTool`): Computes sentiment polarity, emotion ratio, compound score, and overall tone assessment.
   - `text_summarizer_tool` (`TextSummarizerTool`): Generates extractive summaries by scoring and ranking key sentences using term frequency.
   - `diff_tool` (`DiffTool`): Computes line-by-line unified diff patches between two text blocks or files using `difflib`.
   - `keyword_extractor_tool` (`KeywordExtractorTool`): Extracts top keywords, unigrams, bigrams, and TF-IDF scores without external LLM calls.
   - `markdown_to_html_tool` (`MarkdownToHtmlTool`): Renders Markdown to clean HTML with extensions or strips HTML back to Markdown.

5. **`backend/app/tools/modules/utility_tools.py`** (5 Utility Tools):
   - `calculator_tool` (`CalculatorTool`): Evaluates scientific math expressions, algebra, and calculus safely using `sympy` or AST traversal.
   - `datetime_tool` (`DatetimeTool`): Calculates date arithmetic, timezone offsets, ISO timestamps, and date differences.
   - `image_metadata_tool` (`ImageMetadataTool`): Reads image dimensions, format, DPI, and EXIF camera tags via `Pillow`.
   - `hash_crypto_tool` (`HashCryptoTool`): Computes MD5, SHA-256, SHA-512 hashes, Base64 encoding/decoding, and HMAC signatures.
   - `zip_archiver_tool` (`ZipArchiverTool`): Compresses workspace files into ZIP archives, extracts archives, or lists archive contents safely.

6. **`backend/app/tools/modules/dev_tools.py`** (3 Developer Tools):
   - `git_tool` (`GitTool`): Inspects git workspace status, commit history logs, active branch, and diffs via `gitpython` or subprocess CLI fallback.
   - `sql_query_builder_tool` (`SqlQueryBuilderTool`): Cleans, formats, and validates SQL queries using `sqlparse`.
   - `json_schema_validator` (`JsonSchemaValidator`): Validates JSON objects or strings against formal JSON Schema definitions using `jsonschema`.

---

### 2.2 Updated Central Tool Registry (`backend/app/tools/registry.py`)
- Imported all 27 new tool classes from `backend/app/tools/modules/`.
- Aggregated all 27 new tool instances into `ToolRegistry._tools` alongside the original 13 tools.
- `ToolRegistry.list_tools()` now returns 40 registered `BaseTool` instances.

---

### 2.3 Updated Database Tool Seeder (`backend/app/tools/seeder.py`)
- Replaced static 4-item list with dynamic seeding from `tool_registry.list_tools()`.
- Implemented category mapping helper `_determine_category(slug: str)` to auto-categorize all 40 tools into `web`, `document`, `text`, `developer`, or `utility`.
- Database seeder now initializes or updates all 40 tools in the PostgreSQL `tools` table automatically upon backend startup.

---

### 2.4 Updated System Dependencies & Configuration
- Updated `backend/requirements.txt` to include `python-docx`, `openpyxl`, `python-pptx`, `pytesseract`, `pyyaml`, `feedparser`, `dnspython`, `python-whois`, `markdown`, `sympy`, `Pillow`, `gitpython`, `sqlparse`, `jsonschema`, `wikipedia-api`, `nltk`, `sumy`.
- Updated `backend/app/core/config.py` `Settings.Config` to allow `extra = "ignore"`.

---

### 2.5 Verification Script (`backend/test_m2_tools.py`)
- Created automated async verification script testing all 40 registered tools in `ToolRegistry`.
- Confirmed 40/40 tools instantiate and execute `.run(**kwargs)` cleanly without errors.
