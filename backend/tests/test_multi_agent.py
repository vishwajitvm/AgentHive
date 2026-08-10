import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.llm.router import LLMRouter
from app.agents.multi_agent import MultiAgentEngine, multi_agent_engine
from app.agents.models import Agent
from app.core.exceptions import LLMRouteError

@pytest.mark.asyncio
async def test_generate_parallel_fastest_wins():
    """Test that generate_parallel queries providers concurrently and returns the fastest successful result."""
    router = LLMRouter()

    async def slow_mock(*args, **kwargs):
        await asyncio.sleep(0.5)
        return "Slow Provider Response"

    async def fast_mock(*args, **kwargs):
        await asyncio.sleep(0.05)
        return "Fast Provider Response"

    router.providers["gemini"].generate = AsyncMock(side_effect=slow_mock)
    router.providers["groq"].generate = AsyncMock(side_effect=fast_mock)

    result = await router.generate_parallel(
        prompt="Test prompt",
        providers=["gemini", "groq"],
        timeout=5.0
    )

    assert result == "Fast Provider Response"

@pytest.mark.asyncio
async def test_generate_parallel_error_fallback():
    """Test that generate_parallel skips failing providers and returns result from healthy provider."""
    router = LLMRouter()

    async def error_mock(*args, **kwargs):
        raise RuntimeError("Provider Connection Error")

    async def healthy_mock(*args, **kwargs):
        await asyncio.sleep(0.05)
        return "Healthy Provider Response"

    router.providers["gemini"].generate = AsyncMock(side_effect=error_mock)
    router.providers["groq"].generate = AsyncMock(side_effect=healthy_mock)

    result = await router.generate_parallel(
        prompt="Test prompt",
        providers=["gemini", "groq"],
        timeout=5.0
    )

    assert result == "Healthy Provider Response"

@pytest.mark.asyncio
async def test_multi_agent_router_pattern():
    """Test MultiAgentEngine router pattern intent classification and execution."""
    engine = MultiAgentEngine()

    mock_db = AsyncMock()
    agent1 = Agent(id=1, name="Web Search", slug="web_search_agent", agent_type="search", status="active", tools_enabled=["search_tool"])
    agent2 = Agent(id=2, name="Data Analyst", slug="data_analyst", agent_type="analyst", status="active", tools_enabled=["csv_reader_tool"])

    with patch.object(engine, "get_candidate_agents", new_callable=AsyncMock) as mock_candidates, \
         patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_candidates.return_value = [agent1, agent2]
        mock_gen.return_value = '{"selected_agent": "data_analyst", "reasoning": "Query requires data analysis"}'
        mock_exec.return_value = {
            "status": "completed",
            "output": "Analysis complete.",
            "steps_count": 2,
            "elapsed_seconds": 0.5,
            "agent_run_id": 101
        }

        res = await engine.execute_router(query="Analyze sales.csv data", db=mock_db)

        assert res["success"] is True
        assert res["pattern"] == "router"
        assert res["selected_agent"] == "data_analyst"
        assert res["response"] == "Analysis complete."

@pytest.mark.asyncio
async def test_multi_agent_supervisor_pattern():
    """Test MultiAgentEngine supervisor pattern task decomposition and synthesis."""
    engine = MultiAgentEngine()
    mock_db = AsyncMock()

    agent1 = Agent(id=1, name="Web Search", slug="web_search_agent", agent_type="search", status="active")
    agent2 = Agent(id=2, name="Data Analyst", slug="data_analyst", agent_type="analyst", status="active")

    decomp_response = '{"reasoning": "Split search and analysis", "subtasks": [{"agent_slug": "web_search_agent", "sub_query": "Search market trends"}, {"agent_slug": "data_analyst", "sub_query": "Analyze stats"}]}'
    synthesis_response = "Synthesized report combining search and data analysis."

    with patch.object(engine, "get_candidate_agents", new_callable=AsyncMock) as mock_candidates, \
         patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_candidates.return_value = [agent1, agent2]
        mock_gen.side_effect = [decomp_response, synthesis_response]
        mock_exec.return_value = {"status": "completed", "output": "Subtask completed."}

        res = await engine.execute_supervisor(query="Research and analyze market trends", db=mock_db)

        assert res["success"] is True
        assert res["pattern"] == "supervisor"
        assert len(res["subtasks"]) == 2
        assert res["response"] == synthesis_response

@pytest.mark.asyncio
async def test_multi_agent_swarm_pattern_handoff():
    """Test MultiAgentEngine swarm pattern with dynamic agent-to-agent handoffs."""
    engine = MultiAgentEngine()
    mock_db = AsyncMock()

    agent1 = Agent(id=1, name="Debugger", slug="system_debugger", agent_type="debug", status="active")
    agent2 = Agent(id=2, name="Fact Checker", slug="fact_checker_agent", agent_type="fact", status="active")

    with patch.object(engine, "get_candidate_agents", new_callable=AsyncMock) as mock_candidates, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_candidates.return_value = [agent1, agent2]

        # Agent 1 hands off to Agent 2, Agent 2 completes
        mock_exec.side_effect = [
            {"output": '[HANDOFF] fact_checker_agent | {"context": "Verify log output claim"}'},
            {"output": "[ANSWER] {\"reasoning\": \"Claim verified\", \"answer\": \"Verification successful\"}"}
        ]

        res = await engine.execute_swarm(query="Debug log and verify facts", db=mock_db, initial_agent="system_debugger")

        assert res["success"] is True
        assert res["pattern"] == "swarm"
        assert res["handoff_chain"] == ["system_debugger", "fact_checker_agent"]
        assert "Verification successful" in res["response"]

@pytest.mark.asyncio
async def test_orchestrate_api_endpoint():
    """Test POST /api/orchestrate API endpoint response."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    with patch("app.api.routes.orchestrator.multi_agent_engine.orchestrate", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = {
            "success": True,
            "status": "completed",
            "pattern": "supervisor",
            "selected_agent": None,
            "subtasks": [{"agent_slug": "web_search_agent", "sub_query": "search"}],
            "response": "Unified response synthesis",
            "execution_time_seconds": 1.2
        }

        response = client.post("/api/orchestrate", json={
            "prompt": "Test complex prompt",
            "pattern": "supervisor",
            "use_parallel_llm": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pattern"] == "supervisor"
        assert data["response"] == "Unified response synthesis"

