class BaseAgent:
    """Base class for all AgentHive agents."""

    def __init__(self, agent_id: str, name: str):
        self.agent_id = agent_id
        self.name = name

    async def run(self, task):
        raise NotImplementedError
