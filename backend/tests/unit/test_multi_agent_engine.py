import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.multi_agent import MultiAgentEngine, multi_agent_engine
from app.agents.models import Agent
from app.core.exceptions import AgentRunError

@pytest.mark.asyncio
async def test_get_candidate_agents_all(mock_db_session):
    """Test retrieving all active candidate agents when no target filter is specified."""
    engine = MultiAgentEngine()
    candidates = await engine.get_candidate_agents(mock_db_session)
    assert len(candidates) == 5
    slugs = [a.slug for a in candidates]
    assert "general_assistant" in slugs
    assert "web_search_agent" in slugs

@pytest.mark.asyncio
async def test_get_candidate_agents_filtered(mock_db_session):
    """Test candidate agent filtering by slug, name, or ID."""
    engine = MultiAgentEngine()
    filtered = await engine.get_candidate_agents(mock_db_session, target_agents=["data_analyst", "5"])
    assert len(filtered) == 2
    slugs = [a.slug for a in filtered]
    assert "data_analyst" in slugs
    assert "system_debugger" in slugs

@pytest.mark.asyncio
async def test_get_candidate_agents_fallback(mock_db_session):
    """Test that invalid target_agents filter falls back to all active agents."""
    engine = MultiAgentEngine()
    filtered = await engine.get_candidate_agents(mock_db_session, target_agents=["non_existent_agent"])
    assert len(filtered) == 5

@pytest.mark.asyncio
async def test_router_single_candidate(mock_db_session):
    """Test Router pattern with single candidate agent short-circuit."""
    engine = MultiAgentEngine()
    agent = mock_db_session.agents[0]
    
    with patch.object(engine, "get_candidate_agents", new_callable=AsyncMock) as mock_candidates, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:
        
        mock_candidates.return_value = [agent]
        mock_exec.return_value = {"status": "completed", "output": "Single agent direct response", "steps_count": 1, "agent_run_id": 10}

        res = await engine.execute_router(query="Simple question", db=mock_db_session)
        assert res["success"] is True
        assert res["pattern"] == "router"
        assert res["selected_agent"] == agent.slug
        assert res["response"] == "Single agent direct response"

@pytest.mark.asyncio
async def test_router_json_classification(mock_db_session):
    """Test Router pattern intent classification with JSON parsing."""
    engine = MultiAgentEngine()
    
    with patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:
        
        mock_gen.return_value = '```json\n{"selected_agent": "web_search_agent", "reasoning": "User requested web search"}\n```'
        mock_exec.return_value = {"status": "completed", "output": "Web search results", "steps_count": 2, "agent_run_id": 12}

        res = await engine.execute_router(query="Search latest news", db=mock_db_session)
        assert res["success"] is True
        assert res["selected_agent"] == "web_search_agent"
        assert res["reasoning"] == "User requested web search"
        assert res["response"] == "Web search results"

@pytest.mark.asyncio
async def test_router_regex_fallback(mock_db_session):
    """Test Router pattern fallback to regex matching when LLM output is non-standard JSON."""
    engine = MultiAgentEngine()

    with patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_gen.return_value = 'Selection notes: "selected_agent": "data_analyst", reasoning is clear.'
        mock_exec.return_value = {"status": "completed", "output": "Data analysis output"}

        res = await engine.execute_router(query="Calculate statistics", db=mock_db_session)
        assert res["success"] is True
        assert res["selected_agent"] == "data_analyst"

@pytest.mark.asyncio
async def test_router_no_candidates_raises_error():
    """Test that Router raises AgentRunError if no active candidate agents exist."""
    engine = MultiAgentEngine()
    mock_empty_db = AsyncMock()

    with patch.object(engine, "get_candidate_agents", new_callable=AsyncMock) as mock_candidates:
        mock_candidates.return_value = []
        with pytest.raises(AgentRunError):
            await engine.execute_router(query="Hello", db=mock_empty_db)

@pytest.mark.asyncio
async def test_supervisor_pattern_breakdown_and_synthesis(mock_db_session):
    """Test Supervisor pattern task breakdown, subagent execution, and final synthesis."""
    engine = MultiAgentEngine()

    decomp_response = (
        '{\n'
        '  "reasoning": "Decompose into web search and data analysis sub-tasks",\n'
        '  "subtasks": [\n'
        '    {"agent_slug": "web_search_agent", "sub_query": "Fetch latest market data"},\n'
        '    {"agent_slug": "data_analyst", "sub_query": "Analyze market data numbers"}\n'
        '  ]\n'
        '}'
    )
    synthesis_response = "Comprehensive market analysis synthesized from search and statistics."

    with patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_gen.side_effect = [decomp_response, synthesis_response]
        mock_exec.side_effect = [
            {"status": "completed", "output": "Raw market data results"},
            {"status": "completed", "output": "Statistical metrics breakdown"}
        ]

        res = await engine.execute_supervisor(query="Research market trends and stats", db=mock_db_session)

        assert res["success"] is True
        assert res["pattern"] == "supervisor"
        assert len(res["subtasks"]) == 2
        assert res["subagent_results"][0]["agent_slug"] == "web_search_agent"
        assert res["subagent_results"][1]["agent_slug"] == "data_analyst"
        assert res["response"] == synthesis_response

@pytest.mark.asyncio
async def test_supervisor_fallback_to_router_on_json_error(mock_db_session):
    """Test Supervisor falling back to single Router execution when breakdown JSON is invalid."""
    engine = MultiAgentEngine()

    with patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch.object(engine, "execute_router", new_callable=AsyncMock) as mock_router:

        mock_gen.return_value = "Invalid non-JSON response string"
        mock_router.return_value = {"success": True, "pattern": "router", "response": "Router fallback response"}

        res = await engine.execute_supervisor(query="Complex query", db=mock_db_session)
        assert res["response"] == "Router fallback response"
        mock_router.assert_called_once()

@pytest.mark.asyncio
async def test_swarm_pattern_dynamic_handoff_chain(mock_db_session):
    """Test Swarm dynamic multi-agent handoff loop."""
    engine = MultiAgentEngine()

    # Step 1: system_debugger hands off to fact_checker_agent
    # Step 2: fact_checker_agent completes request
    with patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:
        mock_exec.side_effect = [
            {"output": '[HANDOFF] fact_checker_agent | {"context": "Verify log error timestamp domain"}'},
            {"output": '[ANSWER] Domain verified. Logs are legitimate.'}
        ]

        res = await engine.execute_swarm(
            query="Check system logs and verify domain",
            db=mock_db_session,
            initial_agent="system_debugger"
        )

        assert res["success"] is True
        assert res["pattern"] == "swarm"
        assert res["initial_agent"] == "system_debugger"
        assert res["final_agent"] == "fact_checker_agent"
        assert res["handoff_chain"] == ["system_debugger", "fact_checker_agent"]
        assert res["handoffs_count"] == 1
        assert "[ANSWER]" in res["response"]

@pytest.mark.asyncio
async def test_swarm_pattern_max_handoffs_limit(mock_db_session):
    """Test Swarm pattern respect for max_handoffs safety ceiling."""
    engine = MultiAgentEngine()

    with patch("app.agents.multi_agent.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:
        # Alternating handoffs between system_debugger (id=5) and fact_checker_agent (id=4)
        def handoff_side_effect(agent_id, query, db):
            if agent_id == 5:
                return {"output": '[HANDOFF] fact_checker_agent | {"context": "Context to fact checker"}'}
            else:
                return {"output": '[HANDOFF] system_debugger | {"context": "Context to system debugger"}'}

        mock_exec.side_effect = handoff_side_effect

        res = await engine.execute_swarm(
            query="Infinite loop test query",
            db=mock_db_session,
            initial_agent="system_debugger",
            max_handoffs=3
        )

        assert res["success"] is True
        assert res["handoffs_count"] <= 3
        assert "Swarm process concluded after max handoffs" in res["response"]

@pytest.mark.asyncio
async def test_orchestrate_auto_mode_classification(mock_db_session):
    """Test orchestrate() auto pattern selection."""
    engine = MultiAgentEngine()

    with patch.object(engine, "generate_llm", new_callable=AsyncMock) as mock_gen, \
         patch.object(engine, "execute_supervisor", new_callable=AsyncMock) as mock_supervisor:

        mock_gen.return_value = '{"pattern": "supervisor"}'
        mock_supervisor.return_value = {"success": True, "pattern": "supervisor", "response": "Auto supervisor result"}

        res = await engine.orchestrate(query="Complex multi-agent request", db=mock_db_session, pattern="auto")

        assert res["pattern"] == "supervisor"
        assert res["response"] == "Auto supervisor result"
        mock_supervisor.assert_called_once()
