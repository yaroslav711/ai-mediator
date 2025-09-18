"""Abstract interface for AI Agent."""
from abc import ABC, abstractmethod
from typing import Optional, List
from dataclasses import dataclass

from ...domain.entities import SessionMessage, ConversationContext


@dataclass
class AgentResponse:
    """Response from AI agent."""
    pass      # Рекомендация завершить сессию



class AgentInterface(ABC):
    """Abstract interface for AI mediator agent."""
    
    @abstractmethod
    async def process_message(self, context: ConversationContext) -> AgentResponse:
        """
        Process incoming message and generate response.
        
        Args:
            context: Conversation context with message and history
            
        Returns:
            AgentResponse with processed response and recommendations
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if agent is available and healthy."""
        pass
