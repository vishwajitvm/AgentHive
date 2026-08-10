import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.agents.models import Agent
from app.core.database import get_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def override_db_dependency(mock_db_session):
    async def _get_db_override():
        yield mock_db_session

    app.dependency_overrides[get_db] = _get_db_override
    yield
    app.dependency_overrides.clear()

def test_orchestrate_endpoint_success():
    """Test POST /api/orchestrate API endpoint for multi-agent dynamic orchestration."""
    with patch("app.agents.multi_agent.multi_agent_engine.orchestrate", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = {
            "success": True,
            "status": "completed",
            "pattern": "supervisor",
            "selected_agent": None,
            "subtasks": [{"agent_slug": "web_search_agent", "sub_query": "search query"}],
            "response": "Synthesized response from supervisor orchestration.",
            "execution_time_seconds": 1.45
        }

        response = client.post("/api/orchestrate", json={
            "prompt": "Research industry market metrics",
            "pattern": "supervisor",
            "use_parallel_llm": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pattern"] == "supervisor"
        assert data["response"] == "Synthesized response from supervisor orchestration."
        assert data["execution_time_seconds"] == 1.45

def test_orchestrate_endpoint_error_handling():
    """Test POST /api/orchestrate error handling when orchestration fails."""
    with patch("app.agents.multi_agent.multi_agent_engine.orchestrate", new_callable=AsyncMock) as mock_orch:
        mock_orch.side_effect = RuntimeError("LLM routing connection failure")

        response = client.post("/api/orchestrate", json={
            "prompt": "Test query failing",
            "pattern": "router"
        })

        assert response.status_code == 500
        assert "Multi-agent orchestration failed" in response.json()["detail"]

def test_agent_run_endpoint_direct():
    """Test POST /api/agents/{id}/run for direct single-agent execution."""
    with patch("app.api.routes.agents.orchestrator.execute_run", new_callable=AsyncMock) as mock_exec:

        mock_exec.return_value = {
            "status": "completed",
            "output": "Direct agent run output",
            "steps_count": 2,
            "elapsed_seconds": 0.4,
            "agent_run_id": 99
        }

        response = client.post("/api/agents/1/run", json={
            "query": "Direct query",
            "multi_agent_mode": "direct"
        })

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["output"] == "Direct agent run output"

def test_agent_run_endpoint_multi_agent_delegation():
    """Test POST /api/agents/{id}/run delegating to multi-agent engine when multi_agent_mode is specified."""
    with patch("app.agents.multi_agent.multi_agent_engine.orchestrate", new_callable=AsyncMock) as mock_orch:
        mock_orch.return_value = {
            "success": True,
            "status": "completed",
            "pattern": "swarm",
            "response": "Swarm multi-agent execution response",
            "execution_time_seconds": 0.8
        }

        response = client.post("/api/agents/1/run", json={
            "query": "Investigate logs and swarm handoff",
            "multi_agent_mode": "swarm",
            "use_parallel_llm": True
        })

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["pattern"] == "swarm"
        assert data["response"] == "Swarm multi-agent execution response"

def test_agent_run_endpoint_not_found():
    """Test POST /api/agents/{id}/run returning 404 when agent_id does not exist."""
    response = client.post("/api/agents/99999/run", json={
        "query": "Test query"
    })
    assert response.status_code == 404
    assert response.json()["detail"] == "Agent not found."
