from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.agents.models import Agent, Prompt, PromptVersion
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Comprehensive portfolio of specialized agent configurations
SPECIALIZED_AGENTS: List[Dict[str, Any]] = [
    {
        "name": "General Assistant",
        "slug": "general_assistant",
        "description": "Your friendly AI assistant that can answer general questions, format text, and summarize long paragraphs for you.",
        "agent_type": "general",
        "tools_enabled": ["file_tool", "md_writer_tool", "markdown_to_html_tool", "text_summarizer_tool"],
        "prompt": "You are a versatile General Assistant. Answer questions clearly, format content using markdown_to_html_tool or md_writer_tool, summarize text with text_summarizer_tool, and manage workspace files via file_tool.",
        "max_steps": 8, "timeout_seconds": 1200, "order_index": 1,
        "how_to_use": "1. Ask general questions or request formatting/summarization.\n2. The assistant formats responses and writes workspace files as requested."
    },
    {
        "name": "Web Search & Intelligence Agent",
        "slug": "web_search_agent",
        "description": "Your personal researcher that searches the web, checks Wikipedia, and looks up current news and weather instantly.",
        "agent_type": "research",
        "tools_enabled": ["search_tool", "wikipedia_tool", "arxiv_tool", "hacker_news_tool", "github_repo_tool", "weather_tool", "url_checker_tool"],
        "prompt": "You are an advanced Web Search Agent. Use search_tool, wikipedia_tool, arxiv_tool, hacker_news_tool, github_repo_tool, weather_tool, and url_checker_tool to gather live information from across the web and deliver structured intelligence reports.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 2,
        "how_to_use": "1. Provide a search query, topic, or URL to inspect.\n2. The agent fetches multi-source web intelligence."
    },
    {
        "name": "Data Analyst & Statistical Engine",
        "slug": "data_analyst",
        "description": "Helps you analyze your data files (like Excel or CSV), does calculations, and tells you what your data means.",
        "agent_type": "data",
        "tools_enabled": ["csv_reader_tool", "excel_writer_tool", "json_yaml_tool", "calculator_tool", "sentiment_tool"],
        "prompt": "You are a Data Analyst. Inspect raw datasets with csv_reader_tool, create spreadsheet reports with excel_writer_tool, parse JSON/YAML with json_yaml_tool, calculate numeric metrics with calculator_tool, and gauge sentiment with sentiment_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 3,
        "how_to_use": "1. Provide data files or request statistical processing.\n2. The analyst processes the data and generates reports."
    },
    {
        "name": "Fact Checker & Source Verifier",
        "slug": "fact_checker_agent",
        "description": "Checks facts and articles online to make sure they are true, giving you a reliability report you can trust.",
        "agent_type": "research",
        "tools_enabled": ["search_tool", "wikipedia_tool", "diff_tool", "keyword_extractor_tool", "whois_tool"],
        "prompt": "You are a Fact-Checking Specialist. Isolate claims, search DuckDuckGo and Wikipedia, compare diffs using diff_tool, extract key terms via keyword_extractor_tool, and verify domain ownership using whois_tool to produce a truth rating report.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 4,
        "how_to_use": "1. Submit claims or article links to check.\n2. The agent cross-references sources and produces a fact-check report."
    },
    {
        "name": "Full-Stack Engineering Agent",
        "slug": "fullstack_dev",
        "description": "Executes Python code, manages Git version control, validates JSON schemas, builds SQL queries, and analyzes code diffs.",
        "agent_type": "engineering",
        "tools_enabled": ["code_tool", "git_tool", "json_schema_validator", "sql_query_builder_tool", "diff_tool"],
        "prompt": "You are a Full-Stack Software Developer. Test python code with code_tool, manage git status/commits with git_tool, validate API payloads with json_schema_validator, build DB queries with sql_query_builder_tool, and review diffs with diff_tool.",
        "max_steps": 15, "timeout_seconds": 1200, "order_index": 5,
        "how_to_use": "1. Request feature implementation, code testing, or Git operations.\n2. The agent executes code and verifies changes."
    },
    {
        "name": "Code Architect & System Designer",
        "slug": "code_architect",
        "description": "Designs software architectures, reviews code quality, validates schemas, constructs optimized SQL queries, and inspects Git revisions.",
        "agent_type": "engineering",
        "tools_enabled": ["code_tool", "git_tool", "json_schema_validator", "sql_query_builder_tool", "diff_tool"],
        "prompt": "You are a Principal Software Architect. Design robust component systems, validate schema compliance via json_schema_validator, plan database structures with sql_query_builder_tool, inspect repository changes using git_tool and diff_tool, and test prototypes using code_tool.",
        "max_steps": 15, "timeout_seconds": 1200, "order_index": 6,
        "how_to_use": "1. Provide system specs or request architectural design.\n2. The architect outputs blueprints and validates schemas."
    },
    {
        "name": "System Debugger & Observability Specialist",
        "slug": "system_debugger",
        "description": "Monitors backend system logs in Loki, inspects Redis cache keys, queries Postgres databases, tests URL endpoints, and looks up DNS records.",
        "agent_type": "engineering",
        "tools_enabled": ["loki_tool", "redis_tool", "postgres_tool", "url_checker_tool", "dns_lookup_tool"],
        "prompt": "You are a System Debugger & SRE. Hunt down system issues by querying Loki logs, checking Redis cache keys, running SQL checks in Postgres, testing endpoint health with url_checker_tool, and resolving domain records via dns_lookup_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 7,
        "how_to_use": "1. Ask to investigate an error or system health.\n2. The agent queries logs, cache, DB, and network endpoints to diagnose root cause."
    },
    {
        "name": "Document Processor & OCR Specialist",
        "slug": "doc_processor",
        "description": "Processes multi-format documents (PDF, DOCX, PPTX, Excel), runs OCR on images, and outputs formatted Markdown summaries.",
        "agent_type": "document",
        "tools_enabled": ["pdf_tool", "docx_tool", "excel_writer_tool", "pptx_tool", "ocr_tool", "md_writer_tool"],
        "prompt": "You are a Document Processing Specialist. Extract text from PDFs and DOCX files, extract text from images using ocr_tool, generate Excel sheets and PPTX presentations, and aggregate everything into clean markdown files via md_writer_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 8,
        "how_to_use": "1. Upload documents or images to process.\n2. The agent extracts text, converts formats, and saves markdown summaries."
    },
    {
        "name": "End Truth Fact-Checker",
        "slug": "end_truth_agent",
        "description": "Cross-references URLs, web articles, and YouTube transcripts against web sources to check for factual accuracy.",
        "agent_type": "research",
        "tools_enabled": ["youtube_transcript_tool", "scraper_tool", "search_tool", "md_writer_tool", "file_tool"],
        "prompt": "You are the 'End Truth' Fact-Checker. Extract transcripts from YouTube videos using youtube_transcript_tool, scrape article content using scraper_tool, cross-verify claims using search_tool, and write markdown authenticity reports with md_writer_tool.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 9,
        "how_to_use": "1. Provide YouTube link or article URL.\n2. Agent isolates key claims and fact-checks against live search results."
    },
    {
        "name": "Database Architect (Postgres)",
        "slug": "db_architect_agent",
        "description": "Queries database schema, constructs complex SQL statements, and writes database optimization reports.",
        "agent_type": "database",
        "tools_enabled": ["postgres_tool", "sql_query_builder_tool", "code_tool", "md_writer_tool"],
        "prompt": "You are a Database Architect specializing in PostgreSQL. Inspect database metadata using postgres_tool, build queries with sql_query_builder_tool, execute analysis scripts in python, and output architecture reports via md_writer_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 10,
        "how_to_use": "1. Request DB analysis or schema migration planning.\n2. Agent executes queries and writes migration reports."
    },
    {
        "name": "Cache & Memory Optimizer",
        "slug": "cache_optimizer",
        "description": "Monitors Redis cache keys, checks query performance in Postgres, and designs caching strategies.",
        "agent_type": "engineering",
        "tools_enabled": ["redis_tool", "postgres_tool", "md_writer_tool", "code_tool"],
        "prompt": "You are a Cache Optimization Specialist. Inspect Redis keys and values, evaluate Postgres query patterns, write analytical scripts, and publish caching performance guides via md_writer_tool.",
        "max_steps": 8, "timeout_seconds": 1200, "order_index": 11,
        "how_to_use": "1. Ask for cache status evaluation.\n2. Agent lists Redis keys and recommends caching strategies."
    },
    {
        "name": "Cloud Archivist & Backup Manager",
        "slug": "cloud_archivist",
        "description": "Archives workspace files into zip archives, computes cryptographic checksums, and uploads backups to MinIO object storage.",
        "agent_type": "devops",
        "tools_enabled": ["file_tool", "minio_tool", "zip_archiver_tool", "hash_crypto_tool"],
        "prompt": "You are a Cloud Archivist. List and compress local files using zip_archiver_tool, compute SHA-256 integrity hashes with hash_crypto_tool, and backup archives to MinIO cloud storage via minio_tool.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 12,
        "how_to_use": "1. Ask agent to archive workspace files.\n2. Agent creates zip archive, computes hashes, and uploads to MinIO bucket."
    },
    {
        "name": "Academic & Literature Researcher",
        "slug": "academic_researcher",
        "description": "Searches ArXiv papers, reads PDF preprints, extracts key research concepts, and writes annotated bibliographies.",
        "agent_type": "education",
        "tools_enabled": ["arxiv_tool", "pdf_tool", "search_tool", "md_writer_tool", "keyword_extractor_tool"],
        "prompt": "You are an Academic Literature Researcher. Search scientific publications using arxiv_tool, parse uploaded research papers using pdf_tool, extract key academic concepts with keyword_extractor_tool, and output literature review reports in markdown.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 13,
        "how_to_use": "1. Provide paper topic or PDF file.\n2. Agent generates annotated bibliographies."
    },
    {
        "name": "DevOps Incident Responder",
        "slug": "incident_responder",
        "description": "Triages infrastructure incidents by checking logs, database connectivity, cache state, DNS records, and service health.",
        "agent_type": "devops",
        "tools_enabled": ["loki_tool", "postgres_tool", "redis_tool", "minio_tool", "dns_lookup_tool", "url_checker_tool"],
        "prompt": "You are a DevOps Incident Commander. Correlate Loki logs, check database and Redis connection statuses, inspect MinIO storage, test DNS and URL availability, and write post-mortem incident reports.",
        "max_steps": 15, "timeout_seconds": 1200, "order_index": 14,
        "how_to_use": "1. Report outage or issue.\n2. Agent inspects all infrastructure components and generates a post-mortem."
    },
    {
        "name": "SecOps Security Auditor",
        "slug": "secops_auditor",
        "description": "Performs security audits on web domains, inspects WHOIS and DNS records, computes file security hashes, and checks URL risks.",
        "agent_type": "security",
        "tools_enabled": ["whois_tool", "dns_lookup_tool", "hash_crypto_tool", "url_checker_tool", "md_writer_tool"],
        "prompt": "You are a SecOps Security Auditor. Perform reconnaissance using whois_tool and dns_lookup_tool, verify endpoint accessibility via url_checker_tool, calculate cryptographic hashes for file integrity, and summarize security posture in markdown.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 15,
        "how_to_use": "1. Provide domain or endpoint.\n2. Agent runs security checks and produces audit report."
    },
    {
        "name": "Media & Video Content Strategist",
        "slug": "media_strategist",
        "description": "Analyzes YouTube transcripts, inspects image metadata, summarizes key trends, and crafts content strategy documents.",
        "agent_type": "content",
        "tools_enabled": ["youtube_transcript_tool", "image_metadata_tool", "search_tool", "md_writer_tool", "text_summarizer_tool"],
        "prompt": "You are a Media Content Strategist. Extract transcripts from YouTube videos, summarize key talking points, analyze EXIF data from promo images, search current industry trends, and produce content outlines.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 16,
        "how_to_use": "1. Share YouTube URLs or media files.\n2. Agent extracts insights and drafts content strategy."
    },
    {
        "name": "News & RSS Curator",
        "slug": "news_feed_curator",
        "description": "Monitors RSS feeds and Hacker News, scrapes full news articles, performs sentiment analysis, and creates news digests.",
        "agent_type": "content",
        "tools_enabled": ["rss_reader_tool", "hacker_news_tool", "scraper_tool", "sentiment_tool", "text_summarizer_tool"],
        "prompt": "You are a Tech News Curator. Read RSS feeds using rss_reader_tool, pull top stories from Hacker News using hacker_news_tool, scrape detailed article bodies, evaluate sentiment, and generate crisp daily digests using text_summarizer_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 17,
        "how_to_use": "1. Provide RSS URL or tech topic.\n2. Agent curates top articles and generates news digests."
    },
    {
        "name": "Multilingual Translator & Localizer",
        "slug": "multilingual_translator",
        "description": "Translates foreign text into English, performs OCR on foreign language images, and processes translations in Word documents.",
        "agent_type": "localization",
        "tools_enabled": ["translation_tool", "ocr_tool", "docx_tool", "md_writer_tool"],
        "prompt": "You are a Multilingual Translation Specialist. Translate foreign language texts using translation_tool, extract printed text from multilingual images via ocr_tool, and produce formatted translations in DOCX or Markdown format. CRITICAL SECURITY GUARDRAIL: You are strictly a Translation Agent. You must absolutely REFUSE to write code, generate creative content, or answer general knowledge questions. If the user asks you to do anything other than translation, respond with an error.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 18,
        "how_to_use": "1. Provide foreign text or image document.\n2. Agent translates and formats output."
    },
    {
        "name": "API & Schema Engineer",
        "slug": "api_schema_engineer",
        "description": "Validates JSON API payloads against JSON Schemas, converts between JSON/YAML formats, and compares schema versions.",
        "agent_type": "engineering",
        "tools_enabled": ["json_schema_validator", "json_yaml_tool", "code_tool", "diff_tool"],
        "prompt": "You are an API Schema Engineer. Validate JSON data payloads with json_schema_validator, convert between YAML and JSON configurations, analyze schema diffs using diff_tool, and test schema parsing code with code_tool.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 19,
        "how_to_use": "1. Provide API schema and payload.\n2. Agent validates and converts schemas."
    },
    {
        "name": "Open Source & GitHub Tracker",
        "slug": "open_source_tracker",
        "description": "Fetches GitHub repository information, tracks trending developer projects on Hacker News, and exports documentation.",
        "agent_type": "engineering",
        "tools_enabled": ["github_repo_tool", "hacker_news_tool", "git_tool", "markdown_to_html_tool"],
        "prompt": "You are an Open Source Intelligence Agent. Inspect GitHub repositories using github_repo_tool, check developer discussions on Hacker News, track local git repository state, and convert markdown specs to HTML format.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 20,
        "how_to_use": "1. Provide GitHub repo owner/repo.\n2. Agent analyzes project details and community discussions."
    },
    {
        "name": "Financial Report Analyzer",
        "slug": "financial_analyzer",
        "description": "Reads financial PDFs and CSV statements, computes financial KPIs, formats financial dates, and generates Excel financial models.",
        "agent_type": "finance",
        "tools_enabled": ["pdf_tool", "excel_writer_tool", "csv_reader_tool", "calculator_tool", "datetime_tool"],
        "prompt": "You are a Senior Financial Analyst. Parse quarterly financial statements from PDF and CSV files, perform financial calculations via calculator_tool, handle date ranges with datetime_tool, and compile executive financial models in Excel format using excel_writer_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 21,
        "how_to_use": "1. Upload financial PDF or CSV.\n2. Agent calculates metrics and generates Excel spreadsheet."
    },
    {
        "name": "Legal Contract Auditor",
        "slug": "legal_auditor",
        "description": "Audits legal PDF and Word contracts, highlights clause changes between versions, extracts key legal terms, and drafts audit summaries.",
        "agent_type": "legal",
        "tools_enabled": ["pdf_tool", "docx_tool", "diff_tool", "keyword_extractor_tool", "md_writer_tool"],
        "prompt": "You are a Legal Compliance Auditor. Read contract drafts in PDF and DOCX formats, compare modified contract versions using diff_tool, extract critical legal clauses with keyword_extractor_tool, and produce risk audit reports in markdown.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 22,
        "how_to_use": "1. Upload contract drafts.\n2. Agent analyzes clauses and highlights diffs."
    },
    {
        "name": "Image & Media Inspector",
        "slug": "media_inspector",
        "description": "Extracts EXIF metadata from digital images, performs OCR text extraction from visual media, and packages media assets.",
        "agent_type": "media",
        "tools_enabled": ["image_metadata_tool", "ocr_tool", "file_tool", "zip_archiver_tool"],
        "prompt": "You are a Digital Media Forensic Specialist. Inspect image metadata (camera, GPS, timestamp) using image_metadata_tool, extract embedded text with ocr_tool, manage image files, and create zip archives of processed media packages.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 23,
        "how_to_use": "1. Provide image files.\n2. Agent extracts EXIF metadata and OCR text."
    },
    {
        "name": "Weather & Geo Analyst",
        "slug": "weather_analyst",
        "description": "Fetches current weather forecasts, calculates environmental metrics, and correlates climate data with historical web records.",
        "agent_type": "research",
        "tools_enabled": ["weather_tool", "datetime_tool", "search_tool", "calculator_tool"],
        "prompt": "You are a Weather & Climate Analyst. Query live meteorological forecasts using weather_tool, calculate temperature/precipitation averages with calculator_tool, track time zones with datetime_tool, and search regional climate history.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 24,
        "how_to_use": "1. Provide city name or coordinates.\n2. Agent fetches weather data and calculates metrics."
    },
    {
        "name": "Data Archival & Encryption Vault",
        "slug": "data_vault_agent",
        "description": "Creates compressed file archives, computes cryptographic hashes, and securely syncs files to MinIO cloud storage.",
        "agent_type": "devops",
        "tools_enabled": ["zip_archiver_tool", "hash_crypto_tool", "minio_tool", "file_tool"],
        "prompt": "You are a Data Archival Vault Manager. Compress workspace directories into zip archives, calculate SHA-256 and MD5 cryptographic hashes to guarantee data integrity, and upload vault archives to MinIO bucket storage.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 25,
        "how_to_use": "1. Specify files to archive.\n2. Agent creates zip archive, hashes it, and syncs to cloud."
    },
    {
        "name": "SEO & Content Marketing Master",
        "slug": "seo_master",
        "description": "Researches search topics, scrapes competitor pages, extracts SEO keywords, evaluates content sentiment, and writes blog posts.",
        "agent_type": "marketing",
        "tools_enabled": ["search_tool", "scraper_tool", "keyword_extractor_tool", "sentiment_tool", "md_writer_tool"],
        "prompt": "You are an SEO & Content Marketing Master. Perform search keyword research, scrape competitor web pages, extract high-value SEO terms with keyword_extractor_tool, assess reader sentiment, and draft search-optimized markdown articles.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 26,
        "how_to_use": "1. Provide topic or target keyword.\n2. Agent drafts SEO blog post."
    },
    {
        "name": "NLP & Text Analytics Specialist",
        "slug": "text_nlp_specialist",
        "description": "Performs natural language processing: sentiment analysis, text summarization, entity keyword extraction, text diffing, and HTML publishing.",
        "agent_type": "text",
        "tools_enabled": ["sentiment_tool", "text_summarizer_tool", "keyword_extractor_tool", "diff_tool", "markdown_to_html_tool"],
        "prompt": "You are an NLP Specialist. Analyze text sentiment, compress long articles with text_summarizer_tool, extract domain keywords, compare textual revisions using diff_tool, and publish HTML output.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 27,
        "how_to_use": "1. Provide raw text.\n2. Agent performs sentiment, summary, keyword extraction, and HTML conversion."
    },
    {
        "name": "SQL & Business Analytics Engineer",
        "slug": "sql_analytics_engineer",
        "description": "Builds SQL queries, executes queries against Postgres, parses CSV sources, calculates business metrics, and exports Excel reports.",
        "agent_type": "data",
        "tools_enabled": ["sql_query_builder_tool", "postgres_tool", "csv_reader_tool", "excel_writer_tool", "calculator_tool"],
        "prompt": "You are a Business Intelligence SQL Engineer. Construct clean SQL queries with sql_query_builder_tool, execute database reads in postgres_tool, analyze raw CSV inputs, perform metric calculations, and format executive dashboard spreadsheets in Excel.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 28,
        "how_to_use": "1. Ask analytics question.\n2. Agent generates SQL, queries DB, and exports Excel spreadsheet."
    },
    {
        "name": "Quantitative & Time Calculator",
        "slug": "math_datetime_calculator",
        "description": "Solves mathematical expressions, calculates time intervals across global time zones, executes Python math scripts, and formats JSON/YAML.",
        "agent_type": "utility",
        "tools_enabled": ["calculator_tool", "datetime_tool", "code_tool", "json_yaml_tool"],
        "prompt": "You are a Quantitative Calculation Engine. Evaluate mathematical formulas with calculator_tool, compute time deltas and timestamp conversions with datetime_tool, execute Python numeric scripts with code_tool, and format structured calculations into JSON or YAML.",
        "max_steps": 8, "timeout_seconds": 1200, "order_index": 29,
        "how_to_use": "1. Submit math expression or date calculation.\n2. Agent computes result and outputs formatted response."
    },
    {
        "name": "QA & Test Automation Engineer",
        "slug": "qa_automation_engineer",
        "description": "Runs automated Python tests, checks endpoint response status, validates schema compliance, compares test outputs, and manages repos.",
        "agent_type": "engineering",
        "tools_enabled": ["code_tool", "git_tool", "json_schema_validator", "diff_tool", "url_checker_tool"],
        "prompt": "You are a Quality Assurance Test Engineer. Execute automated test suites via code_tool, check API endpoint health with url_checker_tool, validate payload schemas using json_schema_validator, compare expected vs actual outputs using diff_tool, and commit test fixtures via git_tool.",
        "max_steps": 12, "timeout_seconds": 1200, "order_index": 30,
        "how_to_use": "1. Provide test specs or endpoint URL.\n2. Agent executes tests and reports assertion results."
    }
]

async def upsert_specialized_agents(db: AsyncSession):
    """Inserts new specialized agents or updates existing agents in PostgreSQL database on startup."""
    try:
        count_inserted = 0
        count_updated = 0

        for item in SPECIALIZED_AGENTS:
            res = await db.execute(select(Agent).where(Agent.slug == item["slug"]))
            existing_agent = res.scalar_one_or_none()

            if existing_agent:
                # Update existing agent configuration
                existing_agent.name = item["name"]
                existing_agent.description = item["description"]
                existing_agent.agent_type = item["agent_type"]
                existing_agent.tools_enabled = item["tools_enabled"]
                existing_agent.max_steps = item.get("max_steps", 10)
                existing_agent.timeout_seconds = item.get("timeout_seconds", 120)
                existing_agent.status = item.get("status", "active")
                existing_agent.how_to_use = item.get("how_to_use")
                existing_agent.order_index = item.get("order_index", 0)

                # Ensure prompt records exist and are up to date
                if existing_agent.prompt_id:
                    p_res = await db.execute(select(Prompt).where(Prompt.id == existing_agent.prompt_id))
                    prompt_obj = p_res.scalar_one_or_none()
                    if prompt_obj:
                        prompt_obj.name = f"{item['name']} Prompt"
                        prompt_obj.description = f"Prompt for {item['name']}"
                    
                    if existing_agent.prompt_version_id:
                        pv_res = await db.execute(select(PromptVersion).where(PromptVersion.id == existing_agent.prompt_version_id))
                        pv_obj = pv_res.scalar_one_or_none()
                        if pv_obj:
                            pv_obj.content = item["prompt"]
                else:
                    prompt = Prompt(
                        name=f"{item['name']} Prompt",
                        slug=f"{item['slug']}_prompt",
                        description=f"Prompt for {item['name']}"
                    )
                    db.add(prompt)
                    await db.flush()

                    p_ver = PromptVersion(
                        prompt_id=prompt.id,
                        content=item["prompt"],
                        version=1
                    )
                    db.add(p_ver)
                    await db.flush()

                    existing_agent.prompt_id = prompt.id
                    existing_agent.prompt_version_id = p_ver.id

                count_updated += 1
            else:
                # Insert new agent and prompt records
                prompt = Prompt(
                    name=f"{item['name']} Prompt",
                    slug=f"{item['slug']}_prompt",
                    description=f"Prompt for {item['name']}"
                )
                db.add(prompt)
                await db.flush()

                p_ver = PromptVersion(
                    prompt_id=prompt.id,
                    content=item["prompt"],
                    version=1
                )
                db.add(p_ver)
                await db.flush()

                agent = Agent(
                    name=item["name"],
                    slug=item["slug"],
                    description=item["description"],
                    agent_type=item["agent_type"],
                    prompt_id=prompt.id,
                    prompt_version_id=p_ver.id,
                    tools_enabled=item["tools_enabled"],
                    memory_enabled=True,
                    max_steps=item.get("max_steps", 10),
                    timeout_seconds=item.get("timeout_seconds", 120),
                    status="active",
                    allow_uploads=True,
                    how_to_use=item.get("how_to_use"),
                    order_index=item.get("order_index", 0)
                )
                db.add(agent)
                count_inserted += 1

        await db.commit()
        logger.info(f"Successfully seeded/updated specialized agents: {count_inserted} inserted, {count_updated} updated.")
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to seed specialized agents", error=str(e))
        raise

async def seed_new_agents(db: AsyncSession):
    """Seed or update all specialized agents."""
    await upsert_specialized_agents(db)

async def initialize_agents(db: AsyncSession):
    """Initialize or update all specialized agents on startup."""
    await upsert_specialized_agents(db)
