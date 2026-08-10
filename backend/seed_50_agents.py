import asyncio
import os
import json
import logging
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.models import Agent, Prompt, PromptVersion, AgentVersion
from app.agents.seeder import SPECIALIZED_AGENTS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async_engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# Start with the 30 primary specialized agents
AGENTS_DATA = list(SPECIALIZED_AGENTS)

# 20 additional distinct specialized agent definitions (Total 50 specialized agents)
EXTRA_SPECIALIZED_AGENTS = [
    {
        "name": "Presentation Designer",
        "slug": "presentation_designer",
        "description": "Generates PPTX presentations, analyzes image assets, and exports HTML slides.",
        "agent_type": "presentation",
        "tools_enabled": ["pptx_tool", "image_metadata_tool", "markdown_to_html_tool", "file_tool"],
        "prompt": "You are a Presentation Design Specialist. Build PPTX slides, analyze promo image specs, and format HTML slideshows.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 31,
        "how_to_use": "1. Provide slide outline.\n2. Agent creates PPTX presentation and slide decks."
    },
    {
        "name": "Wikipedia Historian & Researcher",
        "slug": "wikipedia_historian",
        "description": "Queries Wikipedia articles, performs web searches, extracts historical terms, and writes research docs.",
        "agent_type": "research",
        "tools_enabled": ["wikipedia_tool", "search_tool", "keyword_extractor_tool", "md_writer_tool"],
        "prompt": "You are a Wikipedia Historian. Search historical events on Wikipedia, verify cross-references, extract key terms, and write historical markdown summaries.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 32,
        "how_to_use": "1. Ask about historical events or figures.\n2. Agent searches Wikipedia and writes detailed articles."
    },
    {
        "name": "GitHub DevOps Monitor",
        "slug": "github_devops_monitor",
        "description": "Monitors GitHub repository activity, local Git branch states, Loki logs, and checks CI/CD endpoints.",
        "agent_type": "devops",
        "tools_enabled": ["github_repo_tool", "git_tool", "loki_tool", "url_checker_tool"],
        "prompt": "You are a DevOps Monitoring Agent. Monitor GitHub repo commits, track local git branches, check Loki build logs, and test deployment URLs.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 33,
        "how_to_use": "1. Provide GitHub repository or CI endpoint.\n2. Agent checks build status and logs."
    },
    {
        "name": "Cryptographic Integrity Checker",
        "slug": "crypto_security_checker",
        "description": "Computes SHA/MD5 hashes, inspects WHOIS records, validates JSON security schemas, and executes Python crypto checks.",
        "agent_type": "security",
        "tools_enabled": ["hash_crypto_tool", "whois_tool", "json_schema_validator", "code_tool"],
        "prompt": "You are a Cryptographic Integrity Checker. Compute SHA-256 and MD5 hashes, verify domain security WHOIS records, and validate cryptographic JSON payloads.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 34,
        "how_to_use": "1. Provide files or payloads to hash/verify.\n2. Agent outputs integrity verification certificates."
    },
    {
        "name": "RSS & News Feed Aggregator",
        "slug": "rss_news_aggregator",
        "description": "Aggregates RSS feeds, scrapes full articles, analyzes sentiment, and generates concise news summaries.",
        "agent_type": "content",
        "tools_enabled": ["rss_reader_tool", "scraper_tool", "sentiment_tool", "text_summarizer_tool"],
        "prompt": "You are an RSS Feed Aggregator. Monitor RSS feeds, scrape article content, analyze media sentiment, and generate crisp executive briefings.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 35,
        "how_to_use": "1. Provide RSS URL.\n2. Agent fetches news feeds and summarizes stories."
    },
    {
        "name": "Hacker News Scout",
        "slug": "hacker_news_scout",
        "description": "Monitors Hacker News frontpage stories, searches developer topics, inspects GitHub links, and writes trend reports.",
        "agent_type": "research",
        "tools_enabled": ["hacker_news_tool", "search_tool", "github_repo_tool", "md_writer_tool"],
        "prompt": "You are a Tech Scout. Fetch top Hacker News items, search developer discussions, inspect linked GitHub repositories, and write markdown trend reports.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 36,
        "how_to_use": "1. Ask for trending tech news.\n2. Agent scouts Hacker News and generates trend summary."
    },
    {
        "name": "PDF Report Summarizer",
        "slug": "pdf_report_summarizer",
        "description": "Reads multi-page PDF documents, summarizes key findings, extracts keywords, and saves summaries to workspace files.",
        "agent_type": "document",
        "tools_enabled": ["pdf_tool", "text_summarizer_tool", "keyword_extractor_tool", "file_tool"],
        "prompt": "You are a PDF Summarizer. Read PDF files from workspace, extract key terms, summarize core arguments, and save notes to workspace files.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 37,
        "how_to_use": "1. Upload PDF report.\n2. Agent extracts key points and saves markdown summaries."
    },
    {
        "name": "Word Document Creator",
        "slug": "word_doc_creator",
        "description": "Creates Word DOCX documents, formats text into HTML/Markdown, and manages local office files.",
        "agent_type": "document",
        "tools_enabled": ["docx_tool", "markdown_to_html_tool", "file_tool", "md_writer_tool"],
        "prompt": "You are a Word Document Author. Build structured DOCX documents, convert Markdown to formatted layouts, and save office files.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 38,
        "how_to_use": "1. Provide content outline.\n2. Agent generates DOCX Word document."
    },
    {
        "name": "Excel Data Exporter",
        "slug": "excel_data_exporter",
        "description": "Reads CSV files, calculates numeric metrics, creates multi-sheet Excel workbooks, and parses JSON data.",
        "agent_type": "data",
        "tools_enabled": ["excel_writer_tool", "csv_reader_tool", "calculator_tool", "json_yaml_tool"],
        "prompt": "You are an Excel Spreadsheet Exporter. Transform raw CSV and JSON data into formatted Excel workbooks with calculated metrics.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 39,
        "how_to_use": "1. Provide CSV or JSON data.\n2. Agent exports formatted XLSX workbook."
    },
    {
        "name": "OCR & Image Transcriber",
        "slug": "ocr_image_transcriber",
        "description": "Runs OCR on scanned image documents, extracts metadata, translates extracted text, and writes output files.",
        "agent_type": "document",
        "tools_enabled": ["ocr_tool", "image_metadata_tool", "translation_tool", "file_tool"],
        "prompt": "You are an OCR Image Transcriber. Extract printed text from images with ocr_tool, inspect EXIF tags, translate foreign text, and save transcribings.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 40,
        "how_to_use": "1. Upload document image.\n2. Agent transcribes text and saves output file."
    },
    {
        "name": "JSON & YAML Config Converter",
        "slug": "json_yaml_converter",
        "description": "Converts between JSON and YAML configuration formats, validates schemas, and checks config file diffs.",
        "agent_type": "engineering",
        "tools_enabled": ["json_yaml_tool", "json_schema_validator", "diff_tool", "file_tool"],
        "prompt": "You are a Config Format Converter. Convert between YAML and JSON, validate against JSON schemas, and compare version diffs.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 41,
        "how_to_use": "1. Provide JSON or YAML config file.\n2. Agent converts format and validates schema."
    },
    {
        "name": "ArXiv Paper Summarizer",
        "slug": "arxiv_paper_summarizer",
        "description": "Searches ArXiv preprints, parses PDF papers, generates research summaries, and publishes markdown notes.",
        "agent_type": "education",
        "tools_enabled": ["arxiv_tool", "pdf_tool", "text_summarizer_tool", "md_writer_tool"],
        "prompt": "You are an ArXiv Paper Summarizer. Search ArXiv for paper topics, parse PDF preprints, generate concise summaries, and publish markdown notes.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 42,
        "how_to_use": "1. Provide paper topic or ArXiv ID.\n2. Agent summarizes paper and saves report."
    },
    {
        "name": "Code Diff Reviewer",
        "slug": "diff_code_reviewer",
        "description": "Analyzes code diffs, reviews Git commits, validates JSON schemas, and executes Python verification scripts.",
        "agent_type": "engineering",
        "tools_enabled": ["diff_tool", "git_tool", "code_tool", "json_schema_validator"],
        "prompt": "You are a Code Review Specialist. Analyze code diffs with diff_tool, check Git commits, validate schema changes, and run python tests.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 43,
        "how_to_use": "1. Provide code diff or commit hash.\n2. Agent performs automated code review."
    },
    {
        "name": "Customer Feedback Sentiment Analyzer",
        "slug": "sentiment_feedback_analyzer",
        "description": "Reads customer survey CSV files, evaluates sentiment scores, summarizes feedback trends, and exports Excel reports.",
        "agent_type": "analytics",
        "tools_enabled": ["sentiment_tool", "csv_reader_tool", "text_summarizer_tool", "excel_writer_tool"],
        "prompt": "You are a Customer Feedback Analyst. Read survey responses in CSV, calculate sentiment scores, summarize feedback themes, and generate Excel reports.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 44,
        "how_to_use": "1. Upload customer feedback CSV.\n2. Agent analyzes sentiment and generates report."
    },
    {
        "name": "Zip & Cloud Vault Manager",
        "slug": "zip_storage_backup",
        "description": "Creates zip archives, calculates cryptographic hashes, manages workspace files, and syncs archives to MinIO cloud storage.",
        "agent_type": "devops",
        "tools_enabled": ["zip_archiver_tool", "minio_tool", "file_tool", "hash_crypto_tool"],
        "prompt": "You are a Storage Vault Manager. Create zip archives, compute cryptographic hashes, and sync workspace archives to MinIO cloud storage.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 45,
        "how_to_use": "1. Specify folder to zip and backup.\n2. Agent compresses, computes hashes, and syncs to MinIO."
    },
    {
        "name": "DNS & WHOIS Recon Agent",
        "slug": "dns_whois_recon",
        "description": "Performs DNS record lookups, queries domain WHOIS metadata, checks URL status, and searches web references.",
        "agent_type": "security",
        "tools_enabled": ["dns_lookup_tool", "whois_tool", "url_checker_tool", "search_tool"],
        "prompt": "You are a Domain Reconnaissance Agent. Query DNS A/MX/TXT records, inspect WHOIS registration data, check URL status, and gather domain intelligence.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 46,
        "how_to_use": "1. Provide domain name.\n2. Agent performs DNS and WHOIS reconnaissance."
    },
    {
        "name": "Redis Cache Inspector",
        "slug": "redis_cache_inspector",
        "description": "Inspects Redis keys, correlates with Postgres tables, runs Python diagnostic scripts, and reviews Loki error logs.",
        "agent_type": "engineering",
        "tools_enabled": ["redis_tool", "postgres_tool", "code_tool", "loki_tool"],
        "prompt": "You are a Redis Cache Inspector. Inspect Redis keys and expiry times, check Postgres query stats, run python scripts, and examine Loki logs for cache misses.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 47,
        "how_to_use": "1. Ask to inspect Redis cache status.\n2. Agent lists keys and correlates with DB state."
    },
    {
        "name": "Postgres Analytics Bot",
        "slug": "postgres_analytics_bot",
        "description": "Builds SQL queries, executes queries against Postgres, parses CSV sources, and writes executive Excel reports.",
        "agent_type": "database",
        "tools_enabled": ["postgres_tool", "sql_query_builder_tool", "csv_reader_tool", "excel_writer_tool"],
        "prompt": "You are a Postgres Analytics Bot. Construct SQL queries, execute database reads, join CSV dataset files, and format multi-sheet Excel reports.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 48,
        "how_to_use": "1. Ask a business analytics query.\n2. Agent queries database and exports Excel report."
    },
    {
        "name": "YouTube Knowledge Extractor",
        "slug": "youtube_knowledge_extractor",
        "description": "Extracts YouTube video transcripts, summarizes content, extracts key topics, and saves markdown knowledge notes.",
        "agent_type": "content",
        "tools_enabled": ["youtube_transcript_tool", "text_summarizer_tool", "keyword_extractor_tool", "md_writer_tool"],
        "prompt": "You are a YouTube Knowledge Extractor. Extract video transcripts, generate structured text summaries, extract key concepts, and save markdown notes.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 49,
        "how_to_use": "1. Provide YouTube video URL.\n2. Agent extracts transcript and generates structured study notes."
    },
    {
        "name": "Universal Document Translator",
        "slug": "universal_translator_bot",
        "description": "Translates foreign text, runs OCR on document scans, translates Word DOCX documents, and reads PDF text.",
        "agent_type": "localization",
        "tools_enabled": ["translation_tool", "ocr_tool", "docx_tool", "pdf_tool"],
        "prompt": "You are a Universal Document Translator. Translate foreign languages into English across text, OCR scans, Word DOCX files, and PDF documents.",
        "max_steps": 10, "timeout_seconds": 1200, "order_index": 50,
        "how_to_use": "1. Provide document in any language.\n2. Agent translates and outputs English text."
    }
]

AGENTS_DATA.extend(EXTRA_SPECIALIZED_AGENTS)

async def main():
    async with AsyncSessionLocal() as db:
        logger.info("Wiping existing agents for a clean slate of 50 specialized agents...")
        await db.execute(delete(Agent))
        await db.execute(delete(Prompt))
        await db.commit()
        
        for item in AGENTS_DATA:
            prompt = Prompt(
                name=f"{item['name']} Prompt",
                slug=f"{item['slug']}_prompt",
                description=f"Prompt for {item['name']}"
            )
            db.add(prompt)
            await db.commit()
            await db.refresh(prompt)
            
            p_ver = PromptVersion(
                prompt_id=prompt.id,
                content=item["prompt"],
                version=1
            )
            db.add(p_ver)
            await db.commit()
            await db.refresh(p_ver)
            
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
            await db.commit()
            
        logger.info(f"Successfully seeded {len(AGENTS_DATA)} valid specialized agents!")

if __name__ == "__main__":
    asyncio.run(main())
