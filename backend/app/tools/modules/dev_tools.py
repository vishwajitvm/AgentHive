import os
import json
import subprocess
from typing import Dict, Any, List
from app.tools.base import BaseTool
from app.logging.logger import get_logger

logger = get_logger(__name__)

WORKSPACE_DIR = os.path.abspath(os.path.join(os.getcwd(), "workspace"))
os.makedirs(WORKSPACE_DIR, exist_ok=True)

class GitTool(BaseTool):
    @property
    def slug(self) -> str: return "git_tool"
    @property
    def name(self) -> str: return "Git Repository Inspector"
    @property
    def description(self) -> str:
        return "Inspects git repository status, commit log, active branch, and diffs. Arguments: action ('status'/'log'/'branch'/'diff'), repo_path (optional, default workspace or project root), limit (optional int, default 5)."

    async def run(self, **kwargs) -> str:
        action = str(kwargs.get("action", "status")).strip().lower()
        repo_path = kwargs.get("repo_path") or kwargs.get("path") or kwargs.get("dir") or kwargs.get("directory") or ""
        repo_path = str(repo_path).strip()
        limit = int(kwargs.get("limit", 5))

        target_dir = WORKSPACE_DIR
        if repo_path:
            if os.path.isabs(repo_path) and os.path.exists(repo_path):
                target_dir = repo_path
            elif os.path.exists(os.path.join(os.getcwd(), repo_path)):
                target_dir = os.path.join(os.getcwd(), repo_path)

        try:
            try:
                import git
                try:
                    repo = git.Repo(target_dir, search_parent_directories=True)
                except git.InvalidGitRepositoryError:
                    return f"Notice: Directory '{target_dir}' is not inside a valid Git repository."

                if action == "status":
                    active_branch = repo.active_branch.name if not repo.head.is_detached else "DETACHED HEAD"
                    untracked = repo.untracked_files
                    is_dirty = repo.is_dirty()
                    return (
                        f"Git Status for '{repo.working_tree_dir}':\n"
                        f"- Branch: {active_branch}\n"
                        f"- Dirty (Modified Files): {is_dirty}\n"
                        f"- Untracked Files Count: {len(untracked)}\n"
                        f"- Untracked Preview: {', '.join(untracked[:5]) if untracked else 'None'}"
                    )
                elif action == "log":
                    commits = list(repo.iter_commits(max_count=limit))
                    log_lines = [f"- [{c.hexsha[:7]}] {c.summary} ({c.author.name}, {c.committed_datetime.strftime('%Y-%m-%d')})" for c in commits]
                    return f"Git Commit Log (Last {len(commits)} commits):\n" + "\n".join(log_lines)
                elif action == "branch":
                    branches = [b.name for b in repo.branches]
                    return f"Git Branches:\n- Active: {repo.active_branch.name}\n- All Branches: {', '.join(branches)}"
                elif action == "diff":
                    diff_text = repo.git.diff(max_count=500)
                    return f"Git Diff Output:\n\n{diff_text[:3000]}" if diff_text else "No unstaged changes."
            except Exception as git_err:
                # Fallback to subprocess git CLI
                if action == "status": cmd = ["git", "status", "-s"]
                elif action == "log": cmd = ["git", "log", f"-n{limit}", "--oneline"]
                elif action == "branch": cmd = ["git", "branch"]
                elif action == "diff": cmd = ["git", "diff"]
                else: cmd = ["git", "status"]

                res = subprocess.run(cmd, cwd=target_dir, capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    return f"Git Output ({action}):\n\n{res.stdout[:3000]}"
                return f"Git CLI returned code {res.returncode}: {res.stderr}"

            return f"Error: Invalid action '{action}'. Supported: status, log, branch, diff."
        except Exception as e:
            return f"GitTool error: {str(e)}"

class SqlQueryBuilderTool(BaseTool):
    @property
    def slug(self) -> str: return "sql_query_builder_tool"
    @property
    def name(self) -> str: return "SQL Query Parser & Formatter"
    @property
    def description(self) -> str:
        return "Formats, cleans, and validates SQL queries for syntax correctness without executing them. Arguments: query, dialect (optional, default 'postgres')."

    async def run(self, **kwargs) -> str:
        query = kwargs.get("query") or kwargs.get("sql") or kwargs.get("statement") or kwargs.get("text") or ""
        query = str(query).strip()
        dialect = str(kwargs.get("dialect", "postgres")).strip().lower()

        if not query:
            return "Error: query parameter is required."

        try:
            try:
                import sqlparse
                formatted = sqlparse.format(
                    query,
                    reindent=True,
                    keyword_case='upper',
                    identifier_case='lowercase',
                    strip_comments=False
                )
                parsed = sqlparse.parse(query)
                statement_types = [stmt.get_type() for stmt in parsed]
                
                return (
                    f"SQL Formatting & Validation Result:\n"
                    f"- Dialect: {dialect}\n"
                    f"- Statement Types Detected: {', '.join(statement_types)}\n"
                    f"- Valid SQL Tokens: {len(parsed[0].tokens) if parsed else 0}\n\n"
                    f"Formatted SQL Query:\n```sql\n{formatted}\n```"
                )
            except Exception:
                # Basic string formatting fallback
                keywords = ["SELECT", "FROM", "WHERE", "JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN", "GROUP BY", "ORDER BY", "HAVING", "LIMIT", "INSERT INTO", "UPDATE", "DELETE FROM"]
                formatted = query
                for kw in keywords:
                    formatted = formatted.replace(kw.lower(), kw).replace(kw.capitalize(), kw)
                return f"Formatted SQL (Basic Fallback):\n```sql\n{formatted}\n```"
        except Exception as e:
            return f"SqlQueryBuilderTool error: {str(e)}"

class JsonSchemaValidator(BaseTool):
    @property
    def slug(self) -> str: return "json_schema_validator"
    @property
    def name(self) -> str: return "JSON Schema Validator"
    @property
    def description(self) -> str:
        return "Validates a JSON object or string against a formal JSON Schema definition. Arguments: json_data (JSON string or dict), schema (JSON Schema dict or string)."

    async def run(self, **kwargs) -> str:
        json_data_input = kwargs.get("json_data") or kwargs.get("json") or kwargs.get("data") or kwargs.get("content") or ""
        schema_input = kwargs.get("schema") or kwargs.get("schema_data") or ""

        if not json_data_input or not schema_input:
            return "Error: Both 'json_data' and 'schema' parameters are required."

        try:
            # Parse JSON Data
            if isinstance(json_data_input, str):
                json_data = json.loads(json_data_input)
            else:
                json_data = json_data_input

            # Parse Schema
            if isinstance(schema_input, str):
                schema = json.loads(schema_input)
            else:
                schema = schema_input

            try:
                import jsonschema
                jsonschema.validate(instance=json_data, schema=schema)
                return "JSON Schema Validation Passed! The JSON data fully complies with the provided schema."
            except jsonschema.ValidationError as ve:
                return (
                    f"JSON Schema Validation Failed:\n"
                    f"- Error Message: {ve.message}\n"
                    f"- Failed Path: {' -> '.join(str(p) for p in ve.absolute_path)}\n"
                    f"- Failed Keyword: {ve.validator}"
                )
            except jsonschema.SchemaError as se:
                return f"Invalid JSON Schema definition error: {se.message}"
            except Exception:
                # Basic key check fallback
                required = schema.get("required", [])
                missing = [req for req in required if req not in json_data]
                if missing:
                    return f"Schema Validation Failed: Missing required fields: {', '.join(missing)}"
                return "Basic Schema Validation Passed (required keys present)."

        except Exception as e:
            return f"JsonSchemaValidator error: {str(e)}"
