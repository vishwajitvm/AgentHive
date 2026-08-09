import pytest
import os
import sys
from unittest.mock import AsyncMock, patch, MagicMock
from app.tools.registry import tool_registry, WORKSPACE_DIR
from app.tools.base import BaseTool

def test_registry_contains_all_40_tools():
    """Verify that ToolRegistry contains exactly 40 registered tools."""
    all_tools = tool_registry.list_tools()
    assert len(all_tools) == 40, f"Expected 40 tools registered in ToolRegistry, found {len(all_tools)}"
    
    # Check that all 40 tools have non-empty slug, name, and description
    for tool in all_tools:
        assert isinstance(tool, BaseTool)
        assert tool.slug and isinstance(tool.slug, str)
        assert tool.name and isinstance(tool.name, str)
        assert tool.description and isinstance(tool.description, str)

@pytest.mark.asyncio
async def test_all_40_tools_instantiate_and_run():
    """Verify that all 40 registered tools can instantiate and execute .run() successfully."""
    all_tools = tool_registry.list_tools()
    os.makedirs(WORKSPACE_DIR, exist_ok=True)

    # Sample test inputs tailored per tool slug
    tool_args = {
        "file_tool": {"action": "list"},
        "postgres_tool": {"query": "SELECT 1"},
        "redis_tool": {"action": "get", "key": "test_key"},
        "minio_tool": {"action": "upload", "object_name": "test.txt", "content": "data"},
        "loki_tool": {"query": '{container="agenthive"}'},
        "code_tool": {"expression": "print(2 + 2)"},
        "scraper_tool": {"url": "http://example.com"},
        "translation_tool": {"text": "Hello world"},
        "youtube_transcript_tool": {"url": "https://youtube.com/watch?v=dQw4w9WgXcQ"},
        "md_writer_tool": {"action": "write", "filename": "test_output.md", "content": "# Test Header"},
        "search_tool": {"query": "Python test search"},
        "pdf_tool": {"filename": "non_existent.pdf"},
        "csv_reader_tool": {"filename": "non_existent.csv"},

        # Web Tools (9)
        "wikipedia_tool": {"query": "Python programming language"},
        "arxiv_tool": {"query": "Artificial Intelligence"},
        "rss_reader_tool": {"url": "http://example.com/rss"},
        "url_checker_tool": {"url": "http://example.com"},
        "weather_tool": {"city": "London"},
        "dns_lookup_tool": {"domain": "example.com"},
        "whois_tool": {"domain": "example.com"},
        "hacker_news_tool": {"query": "Python"},
        "github_repo_tool": {"repo": "python/cpython"},

        # Document Tools (5)
        "docx_tool": {"action": "read", "filename": "non_existent.docx"},
        "excel_writer_tool": {"action": "write", "filename": "test.xlsx", "data": "[{\"a\":1}]"},
        "pptx_tool": {"action": "create", "filename": "test.pptx", "title": "Test Presentation"},
        "ocr_tool": {"filename": "non_existent.png"},
        "json_yaml_tool": {"action": "json_to_yaml", "content": "{\"key\": \"value\"}"},

        # Text Tools (5)
        "sentiment_tool": {"text": "AgentHive is an awesome multi-agent platform!"},
        "text_summarizer_tool": {"text": "AgentHive is a modular multi-agent orchestration architecture supporting 40 specialized tools and speculative LLM racing."},
        "diff_tool": {"text1": "Line 1\nLine 2", "text2": "Line 1\nLine 2 modified"},
        "keyword_extractor_tool": {"text": "FastAPI PostgreSQL Redis Celery Docker multi-agent framework"},
        "markdown_to_html_tool": {"text": "# Title\nThis is a **bold** paragraph."},

        # Utility Tools (5)
        "calculator_tool": {"expression": "100 * 5 + 20"},
        "datetime_tool": {"action": "now"},
        "image_metadata_tool": {"filename": "non_existent.jpg"},
        "hash_crypto_tool": {"text": "agenthive_secret_data", "algorithm": "sha256"},
        "zip_archiver_tool": {"action": "list"},

        # Developer Tools (3)
        "git_tool": {"action": "status"},
        "sql_query_builder_tool": {"table": "agents", "action": "select"},
        "json_schema_validator": {"schema": "{\"type\": \"object\"}", "data": "{\"name\": \"test\"}"}
    }

    # Patch external network/system calls to avoid external dependency failures during unit testing
    mock_httpx_resp = MagicMock()
    mock_httpx_resp.status_code = 200
    mock_httpx_resp.text = "<html><body>Mock Web Page Content</body></html>"
    mock_httpx_resp.json.return_value = {"status": "ok", "result": []}

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_httpx_resp
    mock_client.post.return_value = mock_httpx_resp
    mock_client.put.return_value = mock_httpx_resp
    mock_client.__aenter__.return_value = mock_client

    with patch("httpx.AsyncClient", return_value=mock_client), \
         patch("asyncpg.connect", new_callable=AsyncMock) as mock_pg, \
         patch("redis.asyncio.from_url") as mock_redis:

        mock_redis_client = AsyncMock()
        mock_redis_client.get.return_value = b"mock_value"
        mock_redis_client.keys.return_value = [b"mock_key"]
        mock_redis.return_value = mock_redis_client

        for tool in all_tools:
            args = tool_args.get(tool.slug, {})
            # Execute .run()
            res = await tool.run(**args)
            
            # Assert result is returned as a string and not None/empty exception
            assert res is not None, f"Tool {tool.slug} returned None"
            assert isinstance(res, str), f"Tool {tool.slug} did not return string output, got {type(res)}"
            assert len(res) > 0, f"Tool {tool.slug} returned empty output string"
