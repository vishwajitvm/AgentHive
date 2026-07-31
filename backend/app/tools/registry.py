import os
import sys
import httpx
import json
import logging
from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.logging.logger import get_logger
from app.core.config import settings
import asyncpg
import redis.asyncio as redis
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi

logger = get_logger(__name__)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
os.makedirs(WORKSPACE_DIR, exist_ok=True)

class FileTool(BaseTool):
    @property
    def slug(self) -> str: return "file_tool"
    @property
    def name(self) -> str: return "File System Tool"
    @property
    def description(self) -> str:
        return "Reads, writes, or lists files in the local workspace. Arguments: action (read/write/list), filename (for read/write), content (for write)."

    async def run(self, **kwargs) -> str:
        action = kwargs.get("action", "").lower()
        filename = kwargs.get("filename", "")
        content = kwargs.get("content", "")

        if action not in ["read", "write", "list"]:
            return "Error: Invalid action. Supported: read, write, list."
        if action in ["read", "write"] and not filename:
            return "Error: Filename is required for read/write."

        filepath = os.path.join(WORKSPACE_DIR, os.path.basename(filename)) if filename else WORKSPACE_DIR
        try:
            if action == "write":
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                return f"Successfully wrote {len(content)} chars to {os.path.basename(filepath)}"
            elif action == "read":
                if not os.path.exists(filepath): return f"Error: '{filename}' not found."
                with open(filepath, "r", encoding="utf-8") as f: return f.read()
            elif action == "list":
                files = os.listdir(WORKSPACE_DIR)
                return "Files:\n" + "\n".join([f"- {f}" for f in files]) if files else "Workspace empty."
        except Exception as e:
            return f"FileTool error: {str(e)}"

class PostgresTool(BaseTool):
    @property
    def slug(self) -> str: return "postgres_tool"
    @property
    def name(self) -> str: return "PostgreSQL DB Tool"
    @property
    def description(self) -> str:
        return "Executes read-only SQL queries against the internal AgentHive database. Arguments: query (SQL string)."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query", "").strip()
        if not query: return "Error: query is required."
        if any(keyword in query.lower() for keyword in ["insert", "update", "delete", "drop", "truncate", "alter", "grant"]):
            return "Security Error: Only SELECT queries are permitted."

        try:
            # We connect directly using asyncpg to bypass SQLAlchemy ORM overhead for raw tool queries
            # Replace postgresql+psycopg with postgresql for asyncpg
            dsn = settings.database_url.replace("postgresql+psycopg://", "postgresql://")
            conn = await asyncpg.connect(dsn)
            try:
                # Limit to 100 rows to prevent massive output
                records = await conn.fetch(f"SELECT * FROM ({query}) AS sub LIMIT 100")
                if not records: return "Query executed successfully. 0 rows returned."
                
                output = []
                # Header
                output.append(" | ".join(records[0].keys()))
                output.append("-" * 50)
                # Rows
                for rec in records:
                    output.append(" | ".join(str(val)[:100] for val in rec.values()))
                
                return "\n".join(output)
            finally:
                await conn.close()
        except Exception as e:
            return f"PostgresTool error: {str(e)}"

class RedisTool(BaseTool):
    @property
    def slug(self) -> str: return "redis_tool"
    @property
    def name(self) -> str: return "Redis Cache Tool"
    @property
    def description(self) -> str:
        return "Reads or writes key-value pairs to the internal Redis cache. Arguments: action (get/set/keys), key, value (for set)."

    async def run(self, **kwargs) -> str:
        action = kwargs.get("action", "").lower()
        key = kwargs.get("key", "")
        value = kwargs.get("value", "")

        if action not in ["get", "set", "keys"]: return "Error: Invalid action. Supported: get, set, keys."

        try:
            redis_client = redis.from_url(settings.redis_url)
            if action == "set":
                if not key: return "Error: key is required."
                await redis_client.set(key, value, ex=3600) # 1 hour expiry
                return f"Successfully set '{key}' in Redis."
            elif action == "get":
                if not key: return "Error: key is required."
                val = await redis_client.get(key)
                return f"Value for '{key}': {val.decode('utf-8') if val else 'NULL'}"
            elif action == "keys":
                pattern = key or "*"
                keys = await redis_client.keys(pattern)
                return "Keys:\n" + "\n".join([k.decode('utf-8') for k in keys[:50]])
        except Exception as e:
            return f"RedisTool error: {str(e)}"

class MinioTool(BaseTool):
    @property
    def slug(self) -> str: return "minio_tool"
    @property
    def name(self) -> str: return "MinIO Cloud Storage"
    @property
    def description(self) -> str:
        return "Uploads/downloads files from the internal MinIO object storage. Arguments: action (upload/download), object_name, content (for upload)."

    async def run(self, **kwargs) -> str:
        action = kwargs.get("action", "").lower()
        object_name = kwargs.get("object_name", "")
        content = kwargs.get("content", "")

        if action not in ["upload", "download"]: return "Error: action must be upload or download."
        if not object_name: return "Error: object_name is required."

        minio_url = f"http://{settings.minio_endpoint}/{settings.minio_bucket}/{object_name}"
        auth = httpx.BasicAuth(settings.minio_access_key, settings.minio_secret_key)
        
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                if action == "upload":
                    resp = await client.put(minio_url, content=content.encode("utf-8"), auth=auth)
                    if resp.status_code in [200, 201]: return f"Uploaded '{object_name}' to MinIO."
                    return f"MinIO upload error: {resp.text}"
                elif action == "download":
                    resp = await client.get(minio_url, auth=auth)
                    if resp.status_code == 200: return resp.text
                    return f"MinIO download error: Object not found."
        except Exception as e:
            return f"MinioTool error: {str(e)}"

class LokiTool(BaseTool):
    @property
    def slug(self) -> str: return "loki_tool"
    @property
    def name(self) -> str: return "Loki Log Search"
    @property
    def description(self) -> str:
        return "Queries the Grafana Loki log aggregation server. Arguments: query (LogQL string, e.g. '{container=\"agenthive-backend\"}')."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        if not query: return "Error: query is required."

        try:
            # Query Loki API
            url = f"{settings.loki_url}/loki/api/v1/query"
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url, params={"query": query, "limit": 50})
                if resp.status_code != 200: return f"Loki API error: {resp.text}"
                
                data = resp.json()
                results = data.get("data", {}).get("result", [])
                
                output = []
                for res in results:
                    stream = res.get("stream", {})
                    values = res.get("values", [])
                    output.append(f"--- Stream: {stream} ---")
                    for val in values:
                        output.append(f"[{val[0]}] {val[1]}")
                
                if not output: return "No logs found for query."
                # Truncate if too long
                full_log = "\n".join(output)
                return full_log[:15000] + "\n[TRUNCATED]" if len(full_log) > 15000 else full_log
        except Exception as e:
            return f"LokiTool error: {str(e)}"

class CodeTool(BaseTool):
    @property
    def slug(self) -> str: return "code_tool"
    @property
    def name(self) -> str: return "Python Interpreter"
    @property
    def description(self) -> str:
        return "Executes Python code in a sandboxed environment. Arguments: expression (Python code string)."

    async def run(self, **kwargs) -> str:
        expression = kwargs.get("expression", "")
        if not expression: return "Error: expression is required."

        safe_dict = {"abs": abs, "min": min, "max": max, "sum": sum, "pow": pow, "round": round, "len": len, "list": list, "dict": dict, "json": json, "math": sys.modules.get("math")}
        
        try:
            from io import StringIO
            old_stdout = sys.stdout
            sys.stdout = mystdout = StringIO()
            try:
                exec(expression, {"__builtins__": None}, safe_dict)
                sys.stdout = old_stdout
                out = mystdout.getvalue()
                return out if out else "Executed successfully (no output)."
            except Exception as eval_e:
                sys.stdout = old_stdout
                return f"Execution error: {str(eval_e)}"
        except Exception as e:
            return f"CodeTool error: {str(e)}"

class ScraperTool(BaseTool):
    @property
    def slug(self) -> str: return "scraper_tool"
    @property
    def name(self) -> str: return "Web Scraper"
    @property
    def description(self) -> str:
        return "Scrapes readable text from a URL. Arguments: url."

    async def run(self, **kwargs) -> str:
        url = kwargs.get("url", "")
        if not url: return "Error: url is required."

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200: return f"Error: status {resp.status_code}"
                
                soup = BeautifulSoup(resp.text, 'html.parser')
                for script in soup(["script", "style", "nav", "footer", "header"]): script.extract()
                text = soup.get_text(separator=' ')
                lines = (line.strip() for line in text.splitlines())
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                text = '\n'.join(chunk for chunk in chunks if chunk)
                
                return f"Scraped {url}:\n{text[:15000]}"
        except Exception as e:
            return f"ScraperTool error: {str(e)}"

class YoutubeTranscriptTool(BaseTool):
    @property
    def slug(self) -> str: return "youtube_transcript_tool"
    @property
    def name(self) -> str: return "YouTube Transcript"
    @property
    def description(self) -> str:
        return "Extracts transcript from a YouTube URL. Arguments: url."

    async def run(self, **kwargs) -> str:
        url = kwargs.get("url", "")
        if not url: return "Error: url is required."

        try:
            video_id = None
            if "v=" in url: video_id = url.split("v=")[1][:11]
            elif "youtu.be/" in url: video_id = url.split("youtu.be/")[1][:11]
            elif "/shorts/" in url: video_id = url.split("/shorts/")[1][:11]
            
            if not video_id: return "Error: Invalid YouTube URL."

            res = YouTubeTranscriptApi().fetch(video_id)
            full_text = " ".join([entry.text for entry in res.snippets])
            return f"Transcript for {video_id}:\n{full_text[:15000]}"
        except Exception as e:
            return f"YoutubeTranscriptTool error: {str(e)}"

class MdWriterTool(FileTool):
    @property
    def slug(self) -> str: return "md_writer_tool"
    @property
    def name(self) -> str: return "Markdown Writer"
    @property
    def description(self) -> str:
        return "Writes structured markdown reports. Alias for file_tool. Arguments: action='write', filename, content."

class SearchTool(BaseTool):
    @property
    def slug(self) -> str: return "search_tool"
    @property
    def name(self) -> str: return "Web Search Engine"
    @property
    def description(self) -> str:
        return "Searches DuckDuckGo for query terms. Arguments: query."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query", "")
        if not query: return "Error: query is required."

        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"https://html.duckduckgo.com/html/?q={httpx.QueryParams({'q': query})}", headers=headers)
                if resp.status_code == 200:
                    from re import findall
                    snippets = findall(r'<a class="result__snippet"[^>]*>(.*?)</a>', resp.text)
                    if snippets:
                        cleaned = [s.replace("<b>", "").replace("</b>", "").strip() for s in snippets[:5]]
                        return f"Search Results for '{query}':\n" + "\n".join([f"- {s}" for s in cleaned])
            return "No results found."
        except Exception as e:
            return f"SearchTool error: {str(e)}"

class PdfTool(BaseTool):
    @property
    def slug(self) -> str: return "pdf_tool"
    @property
    def name(self) -> str: return "PDF Reader"
    @property
    def description(self) -> str:
        return "Reads text from a PDF file in the local workspace. Arguments: filename."

    async def run(self, **kwargs) -> str:
        filename = kwargs.get("filename", "")
        if not filename: return "Error: filename is required."
        filepath = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
        if not os.path.exists(filepath): return f"Error: '{filename}' not found in workspace."

        try:
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            text = chr(10).join([page.get_text() for page in doc])
            return f"Extracted text from {filename}:\n{text[:15000]}"
        except Exception as e:
            return f"PdfTool error: {str(e)}"

class CsvReaderTool(BaseTool):
    @property
    def slug(self) -> str: return "csv_reader_tool"
    @property
    def name(self) -> str: return "CSV/Excel Reader"
    @property
    def description(self) -> str:
        return "Reads a CSV or Excel file in the workspace and returns the first 50 rows as markdown. Arguments: filename."

    async def run(self, **kwargs) -> str:
        filename = kwargs.get("filename", "")
        if not filename: return "Error: filename is required."
        filepath = os.path.join(WORKSPACE_DIR, os.path.basename(filename))
        if not os.path.exists(filepath): return f"Error: '{filename}' not found in workspace."

        try:
            import pandas as pd
            if filename.endswith(".csv"): df = pd.read_csv(filepath)
            else: df = pd.read_excel(filepath)
            return f"Data preview ({filename}):\n" + df.head(50).to_markdown()
        except Exception as e:
            return f"CsvReaderTool error: {str(e)}"

class ToolRegistry:
    def __init__(self):
        self._tools = {
            "file_tool": FileTool(),
            "postgres_tool": PostgresTool(),
            "redis_tool": RedisTool(),
            "minio_tool": MinioTool(),
            "loki_tool": LokiTool(),
            "code_tool": CodeTool(),
            "scraper_tool": ScraperTool(),
            "youtube_transcript_tool": YoutubeTranscriptTool(),
            "md_writer_tool": MdWriterTool(),
            "search_tool": SearchTool(),
            "pdf_tool": PdfTool(),
            "csv_reader_tool": CsvReaderTool()
        }

    def get_tool(self, slug: str) -> BaseTool: return self._tools.get(slug.lower())
    def list_tools(self) -> List[BaseTool]: return list(self._tools.values())

tool_registry = ToolRegistry()
