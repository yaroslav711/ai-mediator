"""Session management service."""
from datetime import datetime, timedelta
from typing import Optional
import uuid
import secrets

from ..domain.entities import DialogSession, Participant, InviteLink, SessionStatus, ParticipantRole
from ..repository.interface import SessionRepositoryInterface


class SessionService:
    """Service for managing dialog sessions."""
    
    def __init__(self, session_repo: SessionRepositoryInterface):
        self.session_repo = session_repo
    
    async def create_session(self, telegram_user_id: int, telegram_username: Optional[str]) -> DialogSession:
        """Create new dialog session with initiator."""
        # Check if user already has an active session
        existing_session = await self.session_repo.get_user_active_session(telegram_user_id)
        if existing_session:
            print(f"🔄 User {telegram_user_id} already has active session {existing_session.session_id[:8]}...")
            return existing_session
        
        session_id = str(uuid.uuid4())
        participant_id = str(uuid.uuid4())
        
        # Create session
        session = DialogSession(
            session_id=session_id,
            status=SessionStatus.WAITING_FOR_PARTNER,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=24)  # Session expires in 24 hours
        )
        
        # Create initiator participant
        initiator = Participant(
            participant_id=participant_id,
            session_id=session_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            role=ParticipantRole.INITIATOR,
            joined_at=datetime.utcnow()
        )
        
        await self.session_repo.save_session(session)
        await self.session_repo.save_participant(initiator)
        
        print(f"🎉 Created new session {session_id[:8]}... for user @{telegram_username or telegram_user_id}")
        return session
    
    async def create_invite(self, session_id: str, telegram_user_id: int) -> Optional[InviteLink]:
        """Generate invitation link for session."""
        # Verify user is participant in this session
        participant = await self.session_repo.get_participant_by_telegram_id(session_id, telegram_user_id)
        if not participant:
            print(f"❌ User {telegram_user_id} is not a participant in session {session_id[:8]}...")
            return None
        
        # Generate shorter, Telegram-friendly invite code (only alphanumeric)
        invite_code = secrets.token_hex(12)  # 24 chars, only 0-9 and a-f
        
        invite = InviteLink(
            invite_code=invite_code,
            session_id=session_id,
            created_by=participant.participant_id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=1)  # Invite expires in 1 hour
        )
        
        await self.session_repo.save_invite(invite)
        return invite
    
    async def join_session(
        self, 
        invite_code: str, 
        telegram_user_id: int, 
        telegram_username: Optional[str]
    ) -> bool:
        """Join session using invite code."""
        # Check if user already has an active session
        existing_session = await self.session_repo.get_user_active_session(telegram_user_id)
        if existing_session:
            print(f"❌ User {telegram_user_id} already has active session")
            return False
        
        # Validate invite
        invite = await self.session_repo.get_invite_by_code(invite_code)
        if not invite or invite.is_used or invite.expires_at < datetime.utcnow():
            print(f"❌ Invalid or expired invite: {invite_code}")
            return False
        
        # Check session capacity
        participants = await self.session_repo.get_session_participants(invite.session_id)
        if len(participants) >= 2:
            print(f"❌ Session {invite.session_id[:8]}... is full")
            return False
        
        # Create second participant
        participant_id = str(uuid.uuid4())
        invitee = Participant(
            participant_id=participant_id,
            session_id=invite.session_id,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
            role=ParticipantRole.INVITEE,
            joined_at=datetime.utcnow()
        )
        
        await self.session_repo.save_participant(invitee)
        await self.session_repo.mark_invite_used(invite_code)
        await self.session_repo.update_session_status(invite.session_id, SessionStatus.ACTIVE)
        
        print(f"🎉 User @{telegram_username or telegram_user_id} joined session {invite.session_id[:8]}...")
        return True
    
    async def get_user_active_session(self, telegram_user_id: int) -> Optional[DialogSession]:
        """Get user's current active session."""
        return await self.session_repo.get_user_active_session(telegram_user_id)
