from abc import ABC, abstractmethod
from typing import Any, Dict

from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr

from config import settings


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self):
        api_key = SecretStr(settings.ANTHROPIC_API_KEY.get_secret_value())
        self.llm = ChatAnthropic(
            anthropic_api_key=api_key,
            model_name="claude-3-sonnet"
        )
    
    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the input data and return the result."""
        pass
    
    async def _parse_with_llm(self, prompt: str) -> str:
        """Helper method to parse text with LLM."""
        response = await self.llm.ainvoke(prompt)
        return response.content.strip()
