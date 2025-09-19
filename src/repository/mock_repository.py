"""Mock repository implementation for testing."""
from typing import Dict, List, Optional, Any
from datetime import datetime

from repository.interface import SessionRepositoryInterface
from domain.entities import (
    DialogSession, Participant, InviteLink, SessionMessage, SessionStatus,
    OutboundMessage, GraphCheckpoint, GraphPhase, PendingTarget
)


class MockSessionRepository(SessionRepositoryInterface):
    """In-memory mock implementation of session repository."""
    
    def __init__(self):
        # In-memory storage
        self.sessions: Dict[str, DialogSession] = {}
        self.participants: Dict[str, Participant] = {}
        self.invites: Dict[str, InviteLink] = {}
        self.messages: Dict[str, SessionMessage] = {}

        # LangGraph-specific storage
        self.outbound_messages: Dict[str, OutboundMessage] = {}
        self.graph_checkpoints: Dict[str, GraphCheckpoint] = {}  # thread_id -> latest checkpoint
        self.processed_telegram_messages: set = set()  # telegram_message_ids
        self.thread_sessions: Dict[str, str] = {}  # thread_id -> session_id

        # Indexes for efficient lookups
        self.user_sessions: Dict[int, str] = {}  # telegram_user_id -> session_id
        self.session_participants: Dict[str, List[str]] = {}  # session_id -> [participant_ids]
        self.session_messages: Dict[str, List[str]] = {}  # session_id -> [message_ids]
        self.session_outbound_messages: Dict[str, List[str]] = {}  # session_id -> [outbound_message_ids]
    
    async def save_session(self, session: DialogSession) -> None:
        """Save session to memory."""
        self.sessions[session.session_id] = session
        status_value = session.status.value if session.status else "None"
        print(f"✅ Mock: Saved session {session.session_id[:8]}... status={status_value}")
    
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
    
    # Message-related methods implementation
    async def save_message(self, message: SessionMessage) -> bool:
        """Save message to memory."""
        try:
            self.messages[message.message_id] = message
            
            # Update session messages index
            if message.session_id not in self.session_messages:
                self.session_messages[message.session_id] = []
            self.session_messages[message.session_id].append(message.message_id)
            
            print(f"✅ Mock: Saved message {message.message_id[:8]}... "
                  f"session={message.session_id[:8]}... content='{message.content[:30]}...'")
            return True
        except Exception as e:
            print(f"❌ Mock: Failed to save message: {e}")
            return False
    
    async def get_session_messages(self, session_id: str) -> List[SessionMessage]:
        """Get all messages for a session ordered by timestamp."""
        message_ids = self.session_messages.get(session_id, [])
        messages = []
        
        for message_id in message_ids:
            message = self.messages.get(message_id)
            if message:
                messages.append(message)
        
        # Sort by timestamp
        messages.sort(key=lambda m: m.timestamp)
        return messages
    
    async def mark_message_processed(self, message_id: str) -> None:
        """Mark message as processed by AI agent."""
        message = self.messages.get(message_id)
        if message:
            message.is_processed = True
            print(f"✅ Mock: Marked message {message_id[:8]}... as processed")
    
    async def get_participant_by_id(self, participant_id: str) -> Optional[Participant]:
        """Get participant by their ID."""
        return self.participants.get(participant_id)

    # LangGraph-specific methods implementation
    async def update_session_graph_state(
        self,
        session_id: str,
        thread_id: str,
        phase: GraphPhase,
        pending_for: PendingTarget,
        version: int
    ) -> None:
        """Update session graph state."""
        session = self.sessions.get(session_id)
        if session:
            session.thread_id = thread_id
            session.phase = phase
            session.pending_for = pending_for
            session.graph_state_version = version
            session.updated_at = datetime.utcnow()

            # Update thread -> session mapping
            self.thread_sessions[thread_id] = session_id

            print(f"✅ Mock: Updated session {session_id[:8]}... graph state "
                  f"phase={phase.value} pending_for={pending_for.value} v{version}")

    async def save_graph_checkpoint(self, checkpoint: GraphCheckpoint) -> None:
        """Save graph state checkpoint."""
        self.graph_checkpoints[checkpoint.thread_id] = checkpoint
        print(f"✅ Mock: Saved checkpoint {checkpoint.checkpoint_id[:8]}... "
              f"for thread {checkpoint.thread_id[:8]}... v{checkpoint.version}")

    async def get_graph_checkpoint(self, thread_id: str) -> Optional[GraphCheckpoint]:
        """Get latest graph checkpoint for thread."""
        checkpoint = self.graph_checkpoints.get(thread_id)
        if checkpoint:
            print(f"📖 Mock: Retrieved checkpoint {checkpoint.checkpoint_id[:8]}... "
                  f"for thread {thread_id[:8]}...")
        return checkpoint

    async def save_outbound_message(self, message: OutboundMessage) -> None:
        """Save outbound message for delivery."""
        self.outbound_messages[message.message_id] = message

        # Update session outbound messages index
        if message.session_id not in self.session_outbound_messages:
            self.session_outbound_messages[message.session_id] = []
        self.session_outbound_messages[message.session_id].append(message.message_id)

        print(f"✅ Mock: Saved outbound message {message.message_id[:8]}... "
              f"target={message.target.value} content='{message.content[:30]}...'")

    async def get_pending_outbound_messages(self, session_id: str) -> List[OutboundMessage]:
        """Get undelivered outbound messages."""
        message_ids = self.session_outbound_messages.get(session_id, [])
        pending_messages = []

        for message_id in message_ids:
            message = self.outbound_messages.get(message_id)
            if message and not message.delivered_at:
                pending_messages.append(message)

        # Sort by creation time
        pending_messages.sort(key=lambda m: m.created_at)
        return pending_messages

    async def mark_outbound_delivered(self, message_id: str, telegram_message_ids: Dict[str, int]) -> None:
        """Mark outbound message as delivered."""
        message = self.outbound_messages.get(message_id)
        if message:
            message.delivered_at = datetime.utcnow()
            message.telegram_message_ids = telegram_message_ids
            print(f"✅ Mock: Marked outbound message {message_id[:8]}... as delivered "
                  f"to {len(telegram_message_ids)} participants")

    async def is_message_processed(self, telegram_message_id: int) -> bool:
        """Check if telegram message was already processed (idempotency)."""
        is_processed = telegram_message_id in self.processed_telegram_messages
        if is_processed:
            print(f"🔄 Mock: Telegram message {telegram_message_id} already processed")
        else:
            # Mark as processed
            self.processed_telegram_messages.add(telegram_message_id)
        return is_processed

    async def get_session_by_thread_id(self, thread_id: str) -> Optional[DialogSession]:
        """Get session by LangGraph thread ID."""
        session_id = self.thread_sessions.get(thread_id)
        if session_id:
            return self.sessions.get(session_id)
        return None
