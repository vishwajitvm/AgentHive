import asyncio
import os
import sys
from typing import Set, Dict, Any

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from sqlalchemy import select, func
from app.tools.registry import tool_registry
from app.agents.seeder import SPECIALIZED_AGENTS, initialize_agents, seed_new_agents
from app.agents.models import Agent, Prompt, PromptVersion
from seed_50_agents import AGENTS_DATA as FIFTY_AGENTS

async def test_tool_registry_mapping():
    """Verify that all 40 registered tools exist in ToolRegistry."""
    registered_tools = tool_registry.list_tools()
    registered_slugs: Set[str] = {t.slug.lower() for t in registered_tools}
    
    print(f"[TEST 1] Registered Tools in ToolRegistry: {len(registered_slugs)}")
    assert len(registered_slugs) >= 40, f"Expected at least 40 registered tools, found {len(registered_slugs)}"
    return registered_slugs

async def test_specialized_agents_config(registered_slugs: Set[str]):
    """Verify that specialized agents portfolio is defined with valid tool slugs and required roles."""
    print(f"[TEST 2] Specialized Agents portfolio count: {len(SPECIALIZED_AGENTS)}")
    assert len(SPECIALIZED_AGENTS) >= 25, f"Expected at least 25 specialized agents, found {len(SPECIALIZED_AGENTS)}"
    
    # Required key specialized roles
    required_slugs = {
        "general_assistant",
        "web_search_agent",
        "data_analyst",
        "fact_checker_agent",
        "fullstack_dev",
        "code_architect",
        "system_debugger",
        "doc_processor"
    }
    
    found_slugs = {agent["slug"] for agent in SPECIALIZED_AGENTS}
    missing_required = required_slugs - found_slugs
    assert not missing_required, f"Missing required specialized roles: {missing_required}"
    print(f"[TEST 2] All mandatory specialized agent roles present: {required_slugs}")
    
    # Verify every tool slug mapped across all specialized agents is valid in ToolRegistry
    all_agents_to_check = SPECIALIZED_AGENTS + FIFTY_AGENTS
    invalid_mappings = []
    
    for agent in all_agents_to_check:
        for tool_slug in agent["tools_enabled"]:
            if tool_slug.lower() not in registered_slugs:
                invalid_mappings.append((agent["slug"], tool_slug))
                
    assert not invalid_mappings, f"Found invalid tool mappings: {invalid_mappings}"
    print(f"[TEST 2] All tool slug mappings across all 50 agents belong to valid ToolRegistry tools.")

class MockResult:
    def __init__(self, scalar_val):
        self._scalar_val = scalar_val

    def scalar_one_or_none(self):
        return self._scalar_val

    def scalar(self):
        return self._scalar_val

class MockAsyncSession:
    def __init__(self):
        self.agents: Dict[str, Agent] = {}
        self.prompts_by_id: Dict[int, Prompt] = {}
        self.prompts_by_slug: Dict[str, Prompt] = {}
        self.prompt_versions_by_id: Dict[int, PromptVersion] = {}
        self._next_agent_id = 1
        self._next_prompt_id = 1
        self._next_pv_id = 1

    async def execute(self, stmt):
        stmt_str = str(stmt)
        params = {}
        try:
            params = stmt.compile().params
        except Exception:
            pass

        param_values = list(params.values()) if params else []

        if "FROM agents" in stmt_str:
            if "count(" in stmt_str.lower():
                return MockResult(len(self.agents))
            if param_values:
                target_slug = param_values[0]
                return MockResult(self.agents.get(target_slug))
            return MockResult(None)

        if "FROM prompts" in stmt_str:
            if "count(" in stmt_str.lower():
                return MockResult(len(self.prompts_by_id))
            if param_values:
                target_id = param_values[0]
                return MockResult(self.prompts_by_id.get(target_id))
            return MockResult(None)

        if "FROM prompt_versions" in stmt_str:
            if param_values:
                target_pv_id = param_values[0]
                return MockResult(self.prompt_versions_by_id.get(target_pv_id))
            return MockResult(None)

        return MockResult(None)

    def add(self, obj):
        if isinstance(obj, Prompt):
            if not obj.id:
                obj.id = self._next_prompt_id
                self._next_prompt_id += 1
            self.prompts_by_id[obj.id] = obj
            self.prompts_by_slug[obj.slug] = obj
        elif isinstance(obj, PromptVersion):
            if not obj.id:
                obj.id = self._next_pv_id
                self._next_pv_id += 1
            self.prompt_versions_by_id[obj.id] = obj
        elif isinstance(obj, Agent):
            if not obj.id:
                obj.id = self._next_agent_id
                self._next_agent_id += 1
            self.agents[obj.slug] = obj

    async def flush(self):
        pass

    async def commit(self):
        pass

    async def rollback(self):
        pass

async def test_database_seeding_and_upsert():
    """Verify that initialize_agents and seed_new_agents seed and upsert models correctly into DB."""
    print("[TEST 3] Testing database seeding and upsert logic with MockAsyncSession...")
    
    mock_db = MockAsyncSession()
    
    # First seeding run
    await initialize_agents(mock_db)
    
    agent_count_1 = len(mock_db.agents)
    assert agent_count_1 == len(SPECIALIZED_AGENTS), f"Expected {len(SPECIALIZED_AGENTS)} seeded agents, got {agent_count_1}"
    
    prompt_count_1 = len(mock_db.prompts_by_id)
    assert prompt_count_1 == len(SPECIALIZED_AGENTS), f"Expected {len(SPECIALIZED_AGENTS)} prompts, got {prompt_count_1}"
    
    # Verify general_assistant configuration
    ga_agent = mock_db.agents.get("general_assistant")
    assert ga_agent is not None, "general_assistant not found in seeded agents"
    assert ga_agent.agent_type == "general"
    assert "file_tool" in ga_agent.tools_enabled
    assert "md_writer_tool" in ga_agent.tools_enabled
    
    # Second seeding run (testing idempotency and update/upsert)
    await seed_new_agents(mock_db)
    
    agent_count_2 = len(mock_db.agents)
    assert agent_count_2 == len(SPECIALIZED_AGENTS), f"Upsert changed agent count! Expected {len(SPECIALIZED_AGENTS)}, got {agent_count_2}"
    
    print(f"[TEST 3] Database seeding & upsert verified successfully! Total agents seeded/upserted: {agent_count_2}")

async def main():
    print("==================================================")
    print("   AGENTHIVE M3 SPECIALIZED AGENTS TEST SUITE     ")
    print("==================================================")
    
    registered_slugs = await test_tool_registry_mapping()
    await test_specialized_agents_config(registered_slugs)
    await test_database_seeding_and_upsert()
    
    print("==================================================")
    print("   ALL M3 AGENT VERIFICATION TESTS PASSED!       ")
    print("==================================================")

if __name__ == "__main__":
    asyncio.run(main())
