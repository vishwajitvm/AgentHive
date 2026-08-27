from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.tools.models import Tool
from app.logging.logger import get_logger

logger = get_logger(__name__)

from app.tools.registry import tool_registry

def _determine_category(slug: str) -> str:
    web_slugs = {
        "search_tool", "scraper_tool", "youtube_transcript_tool", "wikipedia_tool",
        "arxiv_tool", "rss_reader_tool", "url_checker_tool", "weather_tool",
        "dns_lookup_tool", "whois_tool", "hacker_news_tool", "github_repo_tool"
    }
    doc_slugs = {
        "md_writer_tool", "pdf_tool", "csv_reader_tool", "docx_tool",
        "excel_writer_tool", "pptx_tool", "ocr_tool", "json_yaml_tool"
    }
    text_slugs = {
        "translation_tool", "sentiment_tool", "text_summarizer_tool",
        "diff_tool", "keyword_extractor_tool", "markdown_to_html_tool"
    }
    dev_slugs = {
        "code_tool", "git_tool", "sql_query_builder_tool", "json_schema_validator"
    }
    
    if slug in web_slugs: return "web"
    if slug in doc_slugs: return "document"
    if slug in text_slugs: return "text"
    if slug in dev_slugs: return "developer"
    return "utility"

async def seed_tools(db: AsyncSession):
    try:
        all_tools = tool_registry.list_tools()
        for t in all_tools:
            res = await db.execute(select(Tool).where(Tool.slug == t.slug))
            existing = res.scalar_one_or_none()
            category = _determine_category(t.slug)
            if not existing:
                tool = Tool(
                    name=t.name,
                    slug=t.slug,
                    description=t.description,
                    category=category,
                    input_schema={},
                    output_schema={},
                    is_enabled=True,
                    requires_auth=False,
                    required_env_keys=[],
                    safe_mock_mode=False
                )
                db.add(tool)
            else:
                existing.name = t.name
                existing.description = t.description
                existing.category = category
        await db.commit()
        logger.info(f"Successfully seeded {len(all_tools)} tools.")
    except Exception as e:
        logger.exception("Failed to seed tools", error=str(e))
        raise

