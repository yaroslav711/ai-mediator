"""Mock repository implementation for testing."""
from typing import Dict, List, Optional
from datetime import datetime

from .interface import SessionRepositoryInterface
from ..domain.entities import DialogSession, Participant, InviteLink, SessionMessage, SessionStatus


class MockSessionRepository(SessionRepositoryInterface):
    """In-memory mock implementation of session repository."""
    
    def __init__(self):
        # In-memory storage
        self.sessions: Dict[str, DialogSession] = {}
        self.participants: Dict[str, Participant] = {}
        self.invites: Dict[str, InviteLink] = {}
        self.messages: Dict[str, SessionMessage] = {}
        
        # Indexes for efficient lookups
        self.user_sessions: Dict[int, str] = {}  # telegram_user_id -> session_id
        self.session_participants: Dict[str, List[str]] = {}  # session_id -> [participant_ids]
    
    async def save_session(self, session: DialogSession) -> None:
        """Save session to memory."""
        self.sessions[session.session_id] = session
        print(f"✅ Mock: Saved session {session.session_id[:8]}... status={session.status.value}")
    
    async def save_participant(self, participant: Participant) -> None:
        """Save participant to memory."""
        self.participants[participant.participant_id] = participant
        
        # Update indexes
        self.user_sessions[participant.telegram_user_id] = participant.session_id
        
        if participant.session_id not in self.session_participants:
            self.session_participants[participant.session_id] = []
        self.session_participants[participant.session_id].append(participant.participant_id)
        
        print(f"✅ Mock: Saved participant @{participant.telegram_username or participant.telegram_user_id} "
              f"role={participant.role.value}")
    
    async def get_user_active_session(self, telegram_user_id: int) -> Optional[DialogSession]:
        """Get user's active session."""
        session_id = self.user_sessions.get(telegram_user_id)
        if not session_id:
            return None
            
        session = self.sessions.get(session_id)
        if not session:
            return None
            
        # Check if session is still active
        if session.status in [SessionStatus.EXPIRED, SessionStatus.COMPLETED]:
            return None
            
        return session
    
    async def get_participant_by_telegram_id(self, session_id: str, telegram_user_id: int) -> Optional[Participant]:
        """Get participant by telegram user id in specific session."""
        participant_ids = self.session_participants.get(session_id, [])
        
        for participant_id in participant_ids:
            participant = self.participants.get(participant_id)
            if participant and participant.telegram_user_id == telegram_user_id:
                return participant
        
        return None
    
    async def get_session_participants(self, session_id: str) -> List[Participant]:
        """Get all participants in session."""
        participant_ids = self.session_participants.get(session_id, [])
        participants = []
        
        for participant_id in participant_ids:
            participant = self.participants.get(participant_id)
            if participant:
                participants.append(participant)
                
        return participants
    
    async def save_invite(self, invite: InviteLink) -> None:
        """Save invite link."""
        self.invites[invite.invite_code] = invite
        print(f"✅ Mock: Saved invite {invite.invite_code}")
    
    async def get_invite_by_code(self, invite_code: str) -> Optional[InviteLink]:
        """Get invite by code."""
        return self.invites.get(invite_code)
    
    async def mark_invite_used(self, invite_code: str) -> None:
        """Mark invite as used."""
        invite = self.invites.get(invite_code)
        if invite:
            invite.is_used = True
            print(f"✅ Mock: Marked invite {invite_code} as used")
    
    async def update_session_status(self, session_id: str, status: SessionStatus) -> None:
        """Update session status."""
        session = self.sessions.get(session_id)
        if session:
            session.status = status
            session.updated_at = datetime.utcnow()
            print(f"✅ Mock: Updated session {session_id[:8]}... status={status.value}")
