from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    """Abstract interface for all AgentHive tools."""

    @property
    @abstractmethod
    def slug(self) -> str:
        """The tool identifier (slug) used in agent configs."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable tool name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Detailed description including arguments, used in LLM prompts."""
        pass

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Executes the tool logic and returns a string result."""
        pass
