import asyncio
import os
import logging
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.agents.models import Agent, Prompt, PromptVersion, AgentVersion

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async_engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

AGENTS_DATA = [
    {
        "name": "End Truth Fact-Checker",
        "slug": "end_truth_agent",
        "description": "Cross-references URLs, articles, and videos against trusted sources to check for factual accuracy.",
        "agent_type": "research",
        "tools_enabled": ["youtube_transcript_tool", "scraper_tool", "search_tool", "md_writer_tool", "file_tool"],
        "prompt": "You are the 'End Truth' Fact-Checker. Given a URL, determine if it is a video or article. Use youtube_transcript_tool or scraper_tool to isolate claims. Fact-check them with search_tool. Return a Markdown report via md_writer_tool.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 1,
        "how_to_use": "1. Provide a YouTube URL or Article link.\n2. The agent extracts claims and searches the web to fact-check."
    },
    {
        "name": "Database Architect (Postgres)",
        "slug": "db_architect_agent",
        "description": "Analyzes the internal AgentHive Postgres database schema and writes reports or migrations.",
        "agent_type": "engineering",
        "tools_enabled": ["postgres_tool", "code_tool", "md_writer_tool", "file_tool"],
        "prompt": "You are a Postgres Database Architect. You can query the database schema (information_schema) using postgres_tool, run python to analyze the structure, and write migration plans via md_writer_tool.",
        "max_steps": 12, "timeout_seconds": 120, "order_index": 2,
        "how_to_use": "1. Ask the agent to analyze the database schema or plan a migration.\n2. It will query the DB and write a report."
    },
    {
        "name": "System Debugger (Loki)",
        "slug": "system_debugger",
        "description": "Hunts down system bugs by correlating Grafana Loki logs with backend Python code execution.",
        "agent_type": "engineering",
        "tools_enabled": ["loki_tool", "search_tool", "code_tool", "md_writer_tool"],
        "prompt": "You are a Senior Systems Reliability Engineer (SRE). Hunt down bugs by querying Loki logs using loki_tool. If you see exceptions, search for them on the web, and write a bug report.",
        "max_steps": 12, "timeout_seconds": 180, "order_index": 3,
        "how_to_use": "1. Ask the agent to find errors for a specific container (e.g. {container=\"agenthive-backend\"}).\n2. It will summarize the bugs."
    },
    {
        "name": "Cache Optimizer (Redis)",
        "slug": "cache_optimizer",
        "description": "Monitors the Redis cache keys and recommends caching strategies.",
        "agent_type": "engineering",
        "tools_enabled": ["redis_tool", "postgres_tool", "md_writer_tool", "code_tool"],
        "prompt": "You are a Performance Engineer. Use redis_tool to list and read cache keys. Query Postgres for slow operations, and write caching strategies.",
        "max_steps": 8, "timeout_seconds": 90, "order_index": 4,
        "how_to_use": "1. Ask the agent to review the Redis cache status.\n2. It will output current keys and propose improvements."
    },
    {
        "name": "Cloud Archivist (MinIO)",
        "slug": "cloud_archivist",
        "description": "Backs up local workspace files to the internal MinIO object storage bucket.",
        "agent_type": "devops",
        "tools_enabled": ["file_tool", "minio_tool", "code_tool"],
        "prompt": "You are a Cloud Archivist. Use file_tool to list local workspace files, then use minio_tool to upload them to the cloud bucket for safekeeping.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 5,
        "how_to_use": "1. Ask the agent to backup your local workspace to MinIO.\n2. It will list local files and upload them."
    },
    {
        "name": "Data Scientist",
        "slug": "data_scientist",
        "description": "Extracts data from the web, processes it with Python pandas, and outputs reports.",
        "agent_type": "data",
        "tools_enabled": ["scraper_tool", "code_tool", "file_tool", "md_writer_tool"],
        "prompt": "You are a Data Scientist. Scrape data from the web, clean it using python code execution (code_tool), and save the results locally.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 6,
        "how_to_use": "1. Provide a data source URL.\n2. The agent will scrape it, run python processing, and save the dataset."
    },
    {
        "name": "DevOps Incident Responder",
        "slug": "incident_responder",
        "description": "Triages active incidents by checking DB state, Cache state, and Logs simultaneously.",
        "agent_type": "devops",
        "tools_enabled": ["loki_tool", "postgres_tool", "redis_tool", "minio_tool", "md_writer_tool"],
        "prompt": "You are an Incident Commander. If a user reports an outage, query Loki, Postgres, and Redis to find the root cause, then write a post-mortem.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 7,
        "how_to_use": "1. Report an issue (e.g., 'Users cannot login').\n2. The agent checks all systems and generates a post-mortem."
    },
    {
        "name": "SEO & Content Master",
        "slug": "seo_master",
        "description": "Analyzes competitor websites and writes highly optimized markdown blog posts.",
        "agent_type": "marketing",
        "tools_enabled": ["search_tool", "scraper_tool", "md_writer_tool", "file_tool"],
        "prompt": "You are an SEO Master. Search the web for topics, scrape competitor articles, analyze keyword density, and write an optimized blog post.",
        "max_steps": 12, "timeout_seconds": 120, "order_index": 8,
        "how_to_use": "1. Provide a topic or keyword.\n2. The agent researches competitors and drafts the blog post."
    },
    {
        "name": "YouTube Content Strategist",
        "slug": "yt_strategist",
        "description": "Pulls transcripts from popular videos to generate hooks, ideas, and scripts.",
        "agent_type": "content",
        "tools_enabled": ["youtube_transcript_tool", "search_tool", "md_writer_tool", "code_tool"],
        "prompt": "You are a YouTube Strategist. Analyze transcripts of popular videos, extract their core hooks, and draft new video scripts in markdown.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 9,
        "how_to_use": "1. Provide a few YouTube video URLs.\n2. The agent analyzes the hooks and proposes new video outlines."
    },
    {
        "name": "Full-Stack Developer",
        "slug": "fullstack_dev",
        "description": "Writes frontend and backend code, tests it locally, and stores it.",
        "agent_type": "engineering",
        "tools_enabled": ["code_tool", "file_tool", "search_tool", "minio_tool"],
        "prompt": "You are a Full Stack Developer. Write code, test logic via code_tool, save files locally, and back up final releases to MinIO.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 10,
        "how_to_use": "1. Ask the agent to build a specific script or mini-app.\n2. It will write, test, and save the code."
    },
    {
        "name": "Financial Document Analyzer",
        "slug": "finance_analyzer",
        "description": "Reads uploaded financial PDFs and CSVs, calculates metrics, and generates markdown reports.",
        "agent_type": "finance",
        "tools_enabled": ["pdf_tool", "csv_reader_tool", "code_tool", "md_writer_tool"],
        "prompt": "You are a Financial Analyst. Extract text from financial PDFs and CSVs, calculate key performance indicators via python code, and output a markdown summary.",
        "max_steps": 12, "timeout_seconds": 150, "order_index": 11,
        "how_to_use": "1. Upload a financial PDF or CSV.\n2. Ask the agent to summarize revenue, expenses, and growth."
    },
    {
        "name": "Legal Contract Summarizer",
        "slug": "legal_summarizer",
        "description": "Reads dense legal PDFs, cross-references clauses online, and simplifies the text.",
        "agent_type": "legal",
        "tools_enabled": ["pdf_tool", "search_tool", "md_writer_tool"],
        "prompt": "You are a Legal Assistant. Extract text from legal PDFs, search for standard contract clauses online, and rewrite the contract in simple English.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 12,
        "how_to_use": "1. Upload a PDF contract.\n2. Ask the agent to summarize liabilities and obligations."
    },
    {
        "name": "Customer Data Cleaner",
        "slug": "data_cleaner",
        "description": "Reads messy customer CSV data, cleans it using Python pandas, and updates the local file.",
        "agent_type": "data",
        "tools_enabled": ["csv_reader_tool", "code_tool", "file_tool"],
        "prompt": "You are a Data Quality Engineer. Read raw CSV files, execute pandas scripts to remove duplicates and fix formatting, then overwrite the file.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 13,
        "how_to_use": "1. Upload a raw CSV.\n2. Instruct the agent to clean the data and save it back."
    },
    {
        "name": "Postgres Query Optimizer",
        "slug": "pg_optimizer",
        "description": "Analyzes slow database queries and recommends indexes and optimizations.",
        "agent_type": "database",
        "tools_enabled": ["postgres_tool", "search_tool", "md_writer_tool"],
        "prompt": "You are a Database Performance Expert. Query the Postgres statistics tables, identify slow queries, search for optimization strategies, and write an index plan.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 14,
        "how_to_use": "1. Ask the agent to analyze the database performance.\n2. Review the markdown index plan."
    },
    {
        "name": "Web Content Aggregator",
        "slug": "content_aggregator",
        "description": "Scrapes multiple websites based on a search query and compiles a unified report.",
        "agent_type": "research",
        "tools_enabled": ["search_tool", "scraper_tool", "md_writer_tool", "file_tool"],
        "prompt": "You are a Content Aggregator. Search for a topic, scrape the top 3 results, synthesize the information, and write a unified markdown report.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 15,
        "how_to_use": "1. Provide a broad topic.\n2. The agent will research, scrape, and aggregate the data."
    },
    {
        "name": "Podcast Researcher",
        "slug": "podcast_researcher",
        "description": "Analyzes YouTube video interviews, extracts key quotes, and prepares interview notes.",
        "agent_type": "content",
        "tools_enabled": ["youtube_transcript_tool", "code_tool", "md_writer_tool"],
        "prompt": "You are a Podcast Producer. Read YouTube transcripts of previous interviews by a guest, extract their most interesting viewpoints, and prepare interview questions.",
        "max_steps": 10, "timeout_seconds": 120, "order_index": 16,
        "how_to_use": "1. Provide a YouTube URL of a guest.\n2. The agent generates a brief and question list."
    },
    {
        "name": "Log Anomaly Detector",
        "slug": "anomaly_detector",
        "description": "Periodically scans Loki logs for anomalous error spikes and caches findings.",
        "agent_type": "security",
        "tools_enabled": ["loki_tool", "redis_tool", "code_tool"],
        "prompt": "You are a Security Analyst. Query Loki for error logs over the last hour. Use python to detect statistical spikes, and save alerts to Redis.",
        "max_steps": 12, "timeout_seconds": 120, "order_index": 17,
        "how_to_use": "1. Instruct the agent to run a log anomaly scan.\n2. It will write any alerts to the Redis cache."
    },
    {
        "name": "Machine Learning Prep Agent",
        "slug": "ml_prep_agent",
        "description": "Prepares CSV data for ML models (encoding, scaling) and uploads to cloud storage.",
        "agent_type": "data",
        "tools_enabled": ["csv_reader_tool", "code_tool", "minio_tool", "file_tool"],
        "prompt": "You are an ML Engineer. Read CSV data, run python to perform feature engineering, save the processed file, and upload it to MinIO.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 18,
        "how_to_use": "1. Upload raw training data.\n2. The agent prepares the data and uploads it to MinIO."
    },
    {
        "name": "Academic Researcher",
        "slug": "academic_researcher",
        "description": "Searches for academic topics, reads uploaded PDFs, and compiles annotated bibliographies.",
        "agent_type": "education",
        "tools_enabled": ["search_tool", "pdf_tool", "md_writer_tool"],
        "prompt": "You are a Research Assistant. Search the web for academic context, read the provided PDFs, and write a heavily cited markdown bibliography.",
        "max_steps": 12, "timeout_seconds": 150, "order_index": 19,
        "how_to_use": "1. Upload a research PDF and provide a topic.\n2. The agent generates an annotated bibliography."
    },
    {
        "name": "Infrastructure Auditor",
        "slug": "infra_auditor",
        "description": "Audits Postgres schemas, MinIO bucket contents, and Redis keys for security risks.",
        "agent_type": "security",
        "tools_enabled": ["postgres_tool", "redis_tool", "minio_tool", "md_writer_tool"],
        "prompt": "You are a Cloud Security Auditor. List databases via postgres_tool, list buckets via minio_tool, and list cache keys via redis_tool. Identify exposed PII and write an audit report.",
        "max_steps": 15, "timeout_seconds": 180, "order_index": 20,
        "how_to_use": "1. Ask the agent to audit the infrastructure.\n2. It scans DB, Cache, and Storage for risks."
    }
]

async def main():
    async with AsyncSessionLocal() as db:
        logger.info("Wiping existing agents for a clean slate...")
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
                max_steps=item["max_steps"],
                timeout_seconds=item["timeout_seconds"],
                status="active",
                allow_uploads=True,
                how_to_use=item["how_to_use"],
                order_index=item["order_index"]
            )
            db.add(agent)
            await db.commit()
            
        logger.info(f"Successfully seeded {len(AGENTS_DATA)} elite agents!")

if __name__ == "__main__":
    asyncio.run(main())
