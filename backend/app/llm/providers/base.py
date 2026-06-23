from abc import ABC, abstractmethod

class BaseLLMProvider(ABC):
    """Abstract interface for all model provider integrations in AgentHive."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str = None,
        max_tokens: int = 2048,
        timeout: float = 60.0,
        model_name: str = None,
        api_key: str = None,
        base_url: str = None
    ) -> str:
        """Sends chat request to the LLM provider and returns the string response."""
        pass
