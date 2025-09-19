"""Repository interfaces."""
from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime

from ..domain.entities import DialogSession, Participant, InviteLink, SessionMessage, SessionStatus


class SessionRepositoryInterface(ABC):
    """Interface for session repository."""
    
    @abstractmethod
    async def save_session(self, session: DialogSession) -> None:
        pass
    
    @abstractmethod
    async def save_participant(self, participant: Participant) -> None:
        pass
    
    @abstractmethod
    async def get_user_active_session(self, telegram_user_id: int) -> Optional[DialogSession]:
        pass
    
    @abstractmethod
    async def get_participant_by_telegram_id(self, session_id: str, telegram_user_id: int) -> Optional[Participant]:
        pass
    
    @abstractmethod
    async def get_session_participants(self, session_id: str) -> List[Participant]:
        pass
    
    @abstractmethod
    async def save_invite(self, invite: InviteLink) -> None:
        pass
    
    @abstractmethod
    async def get_invite_by_code(self, invite_code: str) -> Optional[InviteLink]:
        pass
    
    @abstractmethod
    async def mark_invite_used(self, invite_code: str) -> None:
        pass
    
    @abstractmethod
    async def update_session_status(self, session_id: str, status: SessionStatus) -> None:
        pass
    
    # Message-related methods
    @abstractmethod
    async def save_message(self, message: SessionMessage) -> bool:
        """Save message to repository. Returns True if successful."""
        pass
    
    @abstractmethod
    async def get_session_messages(self, session_id: str) -> List[SessionMessage]:
        """Get all messages for a session ordered by timestamp."""
        pass
    
    @abstractmethod
    async def mark_message_processed(self, message_id: str) -> None:
        """Mark message as processed by AI agent."""
        pass
    
    @abstractmethod
    async def get_participant_by_id(self, participant_id: str) -> Optional[Participant]:
        """Get participant by their ID."""
        pass