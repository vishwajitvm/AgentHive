import asyncio
import os
import sys

# Ensure backend directory is in sys.path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.tools.registry import tool_registry

async def test_all_tools():
    tools = tool_registry.list_tools()
    print(f"Total Tools Registered in ToolRegistry: {len(tools)}")
    assert len(tools) >= 40, f"Expected at least 40 tools, got {len(tools)}"

    test_args = {
        # Original tools
        "file_tool": {"action": "list"},
        "postgres_tool": {"query": "SELECT 1 as test"},
        "redis_tool": {"action": "keys"},
        "minio_tool": {"action": "download", "object_name": "non_existent.txt"},
        "loki_tool": {"query": '{container="agenthive-backend"}'},
        "code_tool": {"expression": "x = 5 + 10; print(x)"},
        "scraper_tool": {"url": "https://example.com"},
        "translation_tool": {"text": "Bonjour le monde"},
        "youtube_transcript_tool": {"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        "md_writer_tool": {"action": "write", "filename": "test_report.md", "content": "# Test Report"},
        "search_tool": {"query": "AgentHive multi-agent framework"},
        "pdf_tool": {"filename": "non_existent.pdf"},
        "csv_reader_tool": {"filename": "non_existent.csv"},

        # Web Tools (9)
        "wikipedia_tool": {"query": "Python (programming language)"},
        "arxiv_tool": {"query": "Multi-agent systems", "max_results": 2},
        "rss_reader_tool": {"url": "https://news.ycombinator.com/rss", "max_items": 2},
        "url_checker_tool": {"url": "https://httpbin.org/status/200"},
        "weather_tool": {"location": "London"},
        "dns_lookup_tool": {"domain": "example.com", "record_type": "A"},
        "whois_tool": {"domain": "example.com"},
        "hacker_news_tool": {"category": "top", "limit": 2},
        "github_repo_tool": {"repo": "python/cpython", "action": "info"},

        # Doc Tools (5)
        "docx_tool": {"action": "create", "filename": "test_doc.docx", "content": "Hello Word Document"},
        "excel_writer_tool": {"filename": "test_sheet.xlsx", "data": [{"id": 1, "name": "AgentHive"}]},
        "pptx_tool": {"action": "create", "filename": "test_deck.pptx", "slides": [{"title": "Slide 1", "bullets": ["Bullet A"]}]},
        "ocr_tool": {"filename": "non_existent_image.png"},
        "json_yaml_tool": {"action": "json_to_yaml", "content": '{"name": "AgentHive", "version": 2}'},

        # Text Tools (5)
        "sentiment_tool": {"text": "AgentHive is an awesome and excellent multi-agent framework!"},
        "text_summarizer_tool": {"text": "Artificial intelligence and multi-agent systems enable complex workflow automation. Agents communicate using protocols and execute tools. AgentHive provides 40+ zero-cost tools."},
        "diff_tool": {"text1": "Line 1\nLine 2", "text2": "Line 1\nLine 2 modified"},
        "keyword_extractor_tool": {"text": "Multi-agent orchestration and automated tool execution in AgentHive framework."},
        "markdown_to_html_tool": {"action": "md_to_html", "content": "# Header 1\n\n**Bold Text**"},

        # Utility Tools (5)
        "calculator_tool": {"expression": "sqrt(144) + 10 * 3"},
        "datetime_tool": {"action": "current"},
        "image_metadata_tool": {"filename": "non_existent.jpg"},
        "hash_crypto_tool": {"action": "hash", "data": "AgentHive Secret Data", "algorithm": "sha256"},
        "zip_archiver_tool": {"action": "compress", "zip_filename": "test_archive.zip", "filenames": ["test_report.md"]},

        # Dev Tools (3)
        "git_tool": {"action": "status"},
        "sql_query_builder_tool": {"query": "select id, name from users where status = 'active'"},
        "json_schema_validator": {"json_data": '{"id": 1, "name": "test"}', "schema": '{"type": "object", "properties": {"id": {"type": "integer"}, "name": {"type": "string"}}, "required": ["id", "name"]}'}
    }

    passed = 0
    failed = 0

    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

    print("\n--- RUNNING EXECUTION TESTS ON ALL 40 TOOLS ---\n")
    for t in tools:
        kwargs = test_args.get(t.slug, {})
        try:
            res = await t.run(**kwargs)
            safe_snippet = res[:100].replace(chr(10), ' ').encode('ascii', errors='replace').decode('ascii')
            print(f"[PASS] Tool '{t.slug}' ({t.name}) returned len={len(res)}: {safe_snippet}...")
            passed += 1
        except Exception as e:
            print(f"[FAIL] Tool '{t.slug}' ({t.name}) failed with error: {str(e)}")
            failed += 1


    print(f"\nTest Summary: Total={len(tools)}, Passed={passed}, Failed={failed}")
    if failed == 0:
        print("ALL 40 TOOLS PASSED EXECUTION VERIFICATION!")

if __name__ == "__main__":
    asyncio.run(test_all_tools())
