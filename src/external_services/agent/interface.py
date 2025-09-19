"""Abstract interface for AI Agent."""
from abc import ABC, abstractmethod
from typing import Optional, List, Literal
from dataclasses import dataclass

from domain.entities import OutboundMessage, PendingTarget, GraphPhase


@dataclass
class AgentResult:
    """Result from LangGraph agent execution."""
    outbox: List[OutboundMessage]           # Messages to deliver
    status: Literal["waiting", "done", "ok"]  # Graph execution status
    phase: Optional[GraphPhase] = None      # Current graph phase
    pending_for: Optional[PendingTarget] = None  # Who graph waits for
    state_snapshot: Optional[dict] = None   # Full graph state for debugging


class AgentInterface(ABC):
    """Abstract interface for AI mediator agent with LangGraph support."""

    @abstractmethod
    async def start_session(self, thread_id: str, participants: List[str]) -> AgentResult:
        """
        Start new mediation session.

        Args:
            thread_id: Unique thread identifier for LangGraph
            participants: List of participant IDs

        Returns:
            AgentResult with initial outbox and status
        """
        pass

    @abstractmethod
    async def resume_session(
        self,
        thread_id: str,
        sender: str,
        message_text: str,
        current_phase: GraphPhase = None,
        sender_role: str = None
    ) -> AgentResult:
        """
        Resume session with user input.

        Args:
            thread_id: Thread to resume
            sender: Participant ID who sent message
            message_text: User message content
            current_phase: Current phase of the session
            sender_role: Role of the sender (USER_1 or USER_2)

        Returns:
            AgentResult with response outbox and updated status
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if agent is available and healthy."""
        pass
