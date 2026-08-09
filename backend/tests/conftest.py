import sys
import os
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Ensure backend directory is added to sys.path so 'app' module imports cleanly
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.agents.models import Agent, Prompt, PromptVersion
from app.llm.models import ModelProvider

class MockScalars:
    """Helper mock for SQLAlchemy result.scalars()."""
    def __init__(self, items):
        self._items = items

    def all(self):
        return list(self._items)

    def first(self):
        return self._items[0] if self._items else None


class MockExecuteResult:
    """Helper mock for SQLAlchemy session.execute() result."""
    def __init__(self, items=None, scalar_val=None):
        self._items = items if items is not None else []
        self._scalar_val = scalar_val

    def scalars(self):
        return MockScalars(self._items)

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalar(self):
        return self._scalar_val if self._scalar_val is not None else (self._items[0] if self._items else None)


class MockAsyncSession:
    """Mock SQLAlchemy AsyncSession for DB operations in unit/integration tests."""
    def __init__(self, agents=None, providers=None):
        self.agents = agents if agents is not None else []
        self.providers = providers if providers is not None else []
        self.added = []
        self.committed = False
        self.rolled_back = False

    async def execute(self, stmt, *args, **kwargs):
        stmt_str = str(stmt).lower()

        # Handle ModelProvider queries
        if "model_providers" in stmt_str or "modelprovider" in stmt_str:
            return MockExecuteResult(items=[])

        # Inspect statement to filter agents by ID or slug if queried
        try:
            params = getattr(stmt, "compile", lambda: None)()
            if params and hasattr(params, "params") and params.params:
                p_map = params.params
                for k, v in p_map.items():
                    if "id" in k.lower():
                        matched = [a for a in self.agents if str(a.id) == str(v)]
                        return MockExecuteResult(items=matched)
                    if "slug" in k.lower():
                        matched = [a for a in self.agents if a.slug.lower() == str(v).lower()]
                        return MockExecuteResult(items=matched)
        except Exception:
            pass

        return MockExecuteResult(items=self.agents)

    def add(self, instance):
        self.added.append(instance)

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.rolled_back = True

    async def flush(self):
        pass

    async def refresh(self, instance):
        if not hasattr(instance, "id") or instance.id is None:
            instance.id = len(self.added) + 100
        return None


@pytest.fixture
def mock_db_session():
    """Provides a MockAsyncSession fixture pre-populated with active test agents."""
    agents = [
        Agent(
            id=1,
            name="General Assistant",
            slug="general_assistant",
            agent_type="general",
            status="active",
            description="General assistant agent",
            tools_enabled=["file_tool", "md_writer_tool"]
        ),
        Agent(
            id=2,
            name="Web Search Agent",
            slug="web_search_agent",
            agent_type="research",
            status="active",
            description="Web research agent",
            tools_enabled=["search_tool", "wikipedia_tool"]
        ),
        Agent(
            id=3,
            name="Data Analyst",
            slug="data_analyst",
            agent_type="data",
            status="active",
            description="Data analysis agent",
            tools_enabled=["csv_reader_tool", "calculator_tool"]
        ),
        Agent(
            id=4,
            name="Fact Checker",
            slug="fact_checker_agent",
            agent_type="research",
            status="active",
            description="Fact checker agent",
            tools_enabled=["diff_tool", "whois_tool"]
        ),
        Agent(
            id=5,
            name="System Debugger",
            slug="system_debugger",
            agent_type="engineering",
            status="active",
            description="System debugger agent",
            tools_enabled=["loki_tool", "redis_tool"]
        )
    ]
    return MockAsyncSession(agents=agents)


@pytest.fixture
def sample_prompts():
    """Sample user prompts for testing different routing/orchestration cases."""
    return {
        "router_query": "Analyze financial metrics from sales.csv data",
        "supervisor_query": "Search latest tech trends and calculate statistical market share",
        "swarm_query": "Investigate server error logs and verify domain WHOIS records",
        "simple_query": "What is the capital of France?"
    }


@pytest.fixture
def sample_agents():
    """List of sample Agent objects for testing candidate filtering."""
    return [
        Agent(id=1, name="General Assistant", slug="general_assistant", agent_type="general", status="active", tools_enabled=["file_tool"]),
        Agent(id=2, name="Web Search", slug="web_search_agent", agent_type="research", status="active", tools_enabled=["search_tool"]),
        Agent(id=3, name="Data Analyst", slug="data_analyst", agent_type="data", status="active", tools_enabled=["csv_reader_tool"]),
        Agent(id=4, name="Fact Checker", slug="fact_checker_agent", agent_type="research", status="active", tools_enabled=["whois_tool"]),
    ]
