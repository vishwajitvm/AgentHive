from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.tools.models import Tool
from app.logging.logger import get_logger

logger = get_logger(__name__)

DEFAULT_TOOLS = [
    {
        "name": "File System Tool",
        "slug": "file_tool",
        "description": "Reads, writes, lists local project files safely.",
        "category": "core",
        "input_schema": {"action": "string", "filename": "string", "content": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "PDF Text Extractor",
        "slug": "pdf_tool",
        "description": "Extracts text from PDF files.",
        "category": "core",
        "input_schema": {"filename": "string"},
        "output_schema": {"text": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "Web Search Tool",
        "slug": "search_tool",
        "description": "Searches web using provider abstraction or mock mode.",
        "category": "core",
        "input_schema": {"query": "string"},
        "output_schema": {"results": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": True
    },
    {
        "name": "Code Interpreter Tool",
        "slug": "code_tool",
        "description": "Runs safe Python snippets with restrictions.",
        "category": "core",
        "input_schema": {"expression": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "MinIO Storage Tool",
        "slug": "storage_tool",
        "description": "Uploads/downloads files from object storage.",
        "category": "core",
        "input_schema": {"action": "string", "object_name": "string", "content": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY"],
        "safe_mock_mode": True
    },
    {
        "name": "PostgreSQL Query Tool",
        "slug": "postgres_tool",
        "description": "Runs safe internal queries only.",
        "category": "database",
        "input_schema": {"query": "string"},
        "output_schema": {"results": "array"},
        "requires_auth": True,
        "required_env_keys": ["DATABASE_URL"],
        "safe_mock_mode": True
    },
    {
        "name": "Redis Cache Tool",
        "slug": "redis_tool",
        "description": "Reads/writes temporary cached values.",
        "category": "database",
        "input_schema": {"action": "string", "key": "string", "value": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["REDIS_URL"],
        "safe_mock_mode": True
    },
    {
        "name": "Email SMTP Tool",
        "slug": "smtp_tool",
        "description": "Sends emails through configured SMTP.",
        "category": "communication",
        "input_schema": {"to": "string", "subject": "string", "body": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASS"],
        "safe_mock_mode": True
    },
    {
        "name": "Gmail Tool",
        "slug": "gmail_tool",
        "description": "Reads/sends Gmail through official OAuth architecture or mock mode.",
        "category": "communication",
        "input_schema": {"action": "string", "to": "string", "subject": "string", "body": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["GMAIL_OAUTH_TOKEN"],
        "safe_mock_mode": True
    },
    {
        "name": "Google Calendar Tool",
        "slug": "calendar_tool",
        "description": "Creates/reads calendar events through official OAuth architecture or mock mode.",
        "category": "communication",
        "input_schema": {"action": "string", "summary": "string", "start_time": "string", "end_time": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["GCAL_OAUTH_TOKEN"],
        "safe_mock_mode": True
    },
    {
        "name": "GitHub Tool",
        "slug": "github_tool",
        "description": "Reads repos, issues, PRs, and commits.",
        "category": "development",
        "input_schema": {"action": "string", "repo": "string", "issue_title": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["GITHUB_TOKEN"],
        "safe_mock_mode": True
    },
    {
        "name": "Markdown Writer Tool",
        "slug": "md_writer_tool",
        "description": "Generates .md reports.",
        "category": "document",
        "input_schema": {"filename": "string", "content": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "DOCX Writer Tool",
        "slug": "docx_writer_tool",
        "description": "Generates Word documents.",
        "category": "document",
        "input_schema": {"filename": "string", "content": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "CSV/Excel Reader Tool",
        "slug": "csv_reader_tool",
        "description": "Reads structured files.",
        "category": "document",
        "input_schema": {"filename": "string"},
        "output_schema": {"data": "array"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "Website Scraper Tool",
        "slug": "scraper_tool",
        "description": "Extracts clean text from safe URLs.",
        "category": "web",
        "input_schema": {"url": "string"},
        "output_schema": {"text": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": True
    },
    {
        "name": "Notification Tool",
        "slug": "notification_tool",
        "description": "Sends dashboard/internal notifications.",
        "category": "communication",
        "input_schema": {"user_id": "string", "message": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "WhatsApp Business Tool",
        "slug": "whatsapp_tool",
        "description": "Architecture for WhatsApp Business Cloud API. Use mock mode if credentials are missing.",
        "category": "social",
        "input_schema": {"to_number": "string", "message": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["WHATSAPP_API_TOKEN", "WHATSAPP_PHONE_NUMBER_ID"],
        "safe_mock_mode": True
    },
    {
        "name": "Instagram Business Tool",
        "slug": "instagram_tool",
        "description": "Architecture for Instagram Graph API. Use mock mode if credentials are missing.",
        "category": "social",
        "input_schema": {"action": "string", "media_url": "string", "caption": "string"},
        "output_schema": {"result": "string"},
        "requires_auth": True,
        "required_env_keys": ["INSTAGRAM_ACCESS_TOKEN", "INSTAGRAM_ACCOUNT_ID"],
        "safe_mock_mode": True
    },
    {
        "name": "Image Analysis Tool",
        "slug": "image_analysis_tool",
        "description": "Extracts metadata or analyzes uploaded images using selected model.",
        "category": "vision",
        "input_schema": {"image_url_or_path": "string"},
        "output_schema": {"analysis": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": True
    },
    {
        "name": "OCR Tool",
        "slug": "ocr_tool",
        "description": "Optional text extraction from images, disabled by default if dependency missing.",
        "category": "vision",
        "input_schema": {"image_path": "string"},
        "output_schema": {"text": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": True
    },
    {
        "name": "API Request Tool",
        "slug": "api_request_tool",
        "description": "Allows controlled HTTP calls to approved domains only.",
        "category": "web",
        "input_schema": {"method": "string", "url": "string", "headers": "dict", "body": "dict"},
        "output_schema": {"response": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": True
    },
    {
        "name": "Document Summarizer Tool",
        "slug": "summarizer_tool",
        "description": "Summarizes long text chunks.",
        "category": "document",
        "input_schema": {"text": "string"},
        "output_schema": {"summary": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "Embedding Tool",
        "slug": "embedding_tool",
        "description": "Creates embeddings using local/free embedding model.",
        "category": "ai",
        "input_schema": {"text": "string"},
        "output_schema": {"vector": "array"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "Vector Search Tool",
        "slug": "vector_search_tool",
        "description": "Searches pgvector memory.",
        "category": "database",
        "input_schema": {"query": "string"},
        "output_schema": {"results": "array"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "Log Search Tool",
        "slug": "log_search_tool",
        "description": "Searches agent/tool/workflow logs.",
        "category": "system",
        "input_schema": {"query": "string"},
        "output_schema": {"logs": "array"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    },
    {
        "name": "YouTube Transcript Tool",
        "slug": "youtube_transcript_tool",
        "description": "Extracts spoken text/transcripts from YouTube video URLs.",
        "category": "web",
        "input_schema": {"url": "string"},
        "output_schema": {"transcript": "string"},
        "requires_auth": False,
        "required_env_keys": [],
        "safe_mock_mode": False
    }
]

async def seed_tools(db: AsyncSession):
    try:
        for t in DEFAULT_TOOLS:
            res = await db.execute(select(Tool).where(Tool.slug == t["slug"]))
            existing = res.scalar_one_or_none()
            if not existing:
                tool = Tool(
                    name=t["name"],
                    slug=t["slug"],
                    description=t["description"],
                    category=t["category"],
                    input_schema=t["input_schema"],
                    output_schema=t["output_schema"],
                    is_enabled=True,
                    requires_auth=t["requires_auth"],
                    required_env_keys=t["required_env_keys"],
                    safe_mock_mode=t["safe_mock_mode"]
                )
                db.add(tool)
        await db.commit()
        logger.info("Successfully seeded tools.")
    except Exception as e:
        logger.exception("Failed to seed tools", error=str(e))
        raise
