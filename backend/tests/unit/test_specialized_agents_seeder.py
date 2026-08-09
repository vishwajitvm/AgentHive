import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agents.seeder import SPECIALIZED_AGENTS, upsert_specialized_agents
from app.tools.registry import tool_registry

def test_specialized_agents_structure_and_tool_mapping():
    """Verify that SPECIALIZED_AGENTS contains all 30 agents and every enabled tool maps to a registered tool."""
    assert len(SPECIALIZED_AGENTS) == 30, f"Expected 30 specialized agents, found {len(SPECIALIZED_AGENTS)}"

    all_registered_slugs = {t.slug.lower() for t in tool_registry.list_tools()}
    agent_slugs = set()

    for agent_cfg in SPECIALIZED_AGENTS:
        # Check required metadata fields
        assert "name" in agent_cfg and agent_cfg["name"]
        assert "slug" in agent_cfg and agent_cfg["slug"]
        assert "agent_type" in agent_cfg and agent_cfg["agent_type"]
        assert "prompt" in agent_cfg and agent_cfg["prompt"]
        assert "tools_enabled" in agent_cfg and isinstance(agent_cfg["tools_enabled"], list)

        # Check unique slugs
        assert agent_cfg["slug"] not in agent_slugs, f"Duplicate agent slug found: {agent_cfg['slug']}"
        agent_slugs.add(agent_cfg["slug"])

        # Check tool mapping validity against tool_registry
        for tool_slug in agent_cfg["tools_enabled"]:
            assert tool_slug.lower() in all_registered_slugs, (
                f"Agent '{agent_cfg['slug']}' references unregistered tool: '{tool_slug}'"
            )

@pytest.mark.asyncio
async def test_upsert_specialized_agents_seeding():
    """Test upsert_specialized_agents executing DB operations for new and existing agents."""
    mock_db = AsyncMock()
    
    # Simulate DB where execute returns scalar_one_or_none as None (all new insertions)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    await upsert_specialized_agents(mock_db)

    # Verify db.commit() was called to commit seeded agents
    mock_db.commit.assert_called_once()
    # Verify db.add() was called for prompts, prompt versions, and agent records
    assert mock_db.add.call_count >= 30 * 3
