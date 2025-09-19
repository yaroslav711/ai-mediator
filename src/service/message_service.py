"""Unified message service with LangGraph integration."""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from domain.entities import (
    SessionMessage, DialogSession, DialogRole, PendingTarget, GraphPhase,
    OutboundMessage, GraphCheckpoint, Participant, SessionStatus
)
from repository.interface import SessionRepositoryInterface
from external_services.agent.interface import AgentInterface, AgentResult

logger = logging.getLogger(__name__)


class MessageService:
    """Unified service for LangGraph-based mediation with simplified architecture."""

    def __init__(
        self,
        session_repo: SessionRepositoryInterface,
        agent: AgentInterface
    ):
        self.session_repo = session_repo
        self.agent = agent
    
    async def start_mediation_session(
        self,
        session_id: str,
        participants: List[str]
    ) -> Optional[AgentResult]:
        """
        Start new mediation session.

        Args:
            session_id: Session ID
            participants: List of participant IDs

        Returns:
            AgentResult with initial outbox and status
        """
        try:
            # Get session to initialize thread_id
            session = await self._get_or_create_thread_id(session_id)
            if not session or not session.thread_id:
                logger.error(f"Failed to get thread_id for session {session_id}")
                return None

            # Start agent session
            result = await self.agent.start_session(session.thread_id, participants)

            # Save graph state
            await self._save_graph_state(session_id, session.thread_id, result)

            # Save outbound messages
            await self._save_outbound_messages(session_id, result.outbox)

            logger.info(f"Started mediation session {session_id} with thread {session.thread_id}")
            return result

        except Exception as e:
            logger.error(f"Error starting mediation session {session_id}: {e}")
            return None

    async def resume_user_message(
        self,
        session_id: str,
        participant_id: str,
        telegram_message_id: int,
        content: str
    ) -> Optional[AgentResult]:
        """
        Resume session with user input.

        Args:
            session_id: Session ID
            participant_id: ID of message sender
            telegram_message_id: Telegram message ID
            content: Message text content

        Returns:
            AgentResult with response outbox and updated status
        """
        try:
            # Check idempotency
            if await self.session_repo.is_message_processed(telegram_message_id):
                logger.info(f"Message {telegram_message_id} already processed, skipping")
                return None

            # Get session and validate state
            thread_id = await self._get_thread_id(session_id)
            session = await self.session_repo.get_session_by_thread_id(thread_id)
            if not session:
                logger.error(f"Session {session_id} not found by thread_id {thread_id}")
                return None

            # Validate pending_for
            sender_role = await self._get_participant_role(participant_id, session_id)
            if not await self._validate_pending_expectation(session, sender_role):
                logger.warning(f"Message from {participant_id} not expected in phase {session.phase}")
                # Save message but don't process
                await self._save_incoming_message(session_id, participant_id, telegram_message_id, content)
                return None

            # Save incoming message
            message = await self._save_incoming_message(
                session_id, participant_id, telegram_message_id, content
            )
            if not message:
                logger.error(f"Failed to save message for session {session_id}")
                return None

            # Resume agent session with current state
            result = await self.agent.resume_session(
                session.thread_id,
                participant_id,
                content,
                current_phase=session.phase,
                sender_role=sender_role.value
            )

            # Save updated graph state
            await self._save_graph_state(session_id, session.thread_id, result)

            # Save outbound messages
            await self._save_outbound_messages(session_id, result.outbox)

            # Mark message as processed
            await self.session_repo.mark_message_processed(message.message_id)

            logger.info(f"Resumed session {session_id} with message from {participant_id}")
            return result

        except Exception as e:
            logger.error(f"Error resuming session {session_id}: {e}")
            return None
    
    async def get_pending_outbound_messages(self, session_id: str) -> List[OutboundMessage]:
        """Get undelivered outbound messages for session."""
        return await self.session_repo.get_pending_outbound_messages(session_id)

    async def mark_outbound_delivered(
        self,
        message_id: str,
        telegram_message_ids: dict
    ) -> None:
        """Mark outbound message as delivered."""
        await self.session_repo.mark_outbound_delivered(message_id, telegram_message_ids)

    async def _get_or_create_thread_id(self, session_id: str) -> Optional[DialogSession]:
        """Get session and ensure it has thread_id."""
        # Simple mapping: thread_id = session_id for now
        return DialogSession(
            session_id=session_id,
            thread_id=session_id,
            status=None,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    async def _get_thread_id(self, session_id: str) -> str:
        """Get thread_id for session."""
        return session_id

    async def _save_incoming_message(
        self,
        session_id: str,
        participant_id: str,
        telegram_message_id: int,
        content: str
    ) -> Optional[SessionMessage]:
        """Save incoming user message."""
        role = await self._get_participant_role(participant_id, session_id)

        message = SessionMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            participant_id=participant_id,
            role=role,
            telegram_message_id=telegram_message_id,
            content=content,
            timestamp=datetime.utcnow(),
            is_processed=False
        )

        success = await self.session_repo.save_message(message)
        return message if success else None

    async def _save_graph_state(
        self,
        session_id: str,
        thread_id: str,
        result: AgentResult
    ) -> None:
        """Save updated graph state to repository."""
        if result.phase and result.pending_for:
            await self.session_repo.update_session_graph_state(
                session_id=session_id,
                thread_id=thread_id,
                phase=result.phase,
                pending_for=result.pending_for,
                version=1  # Should increment based on current version
            )

    async def _save_outbound_messages(
        self,
        session_id: str,
        outbox: List[OutboundMessage]
    ) -> None:
        """Save outbound messages for delivery."""
        for message in outbox:
            await self.session_repo.save_outbound_message(message)

    async def _get_participant_role(self, participant_id: str, session_id: str) -> DialogRole:
        """Get participant's dialog role."""
        participant = await self.session_repo.get_participant_by_id(participant_id)
        if not participant:
            return DialogRole.USER_1  # Default

        # Map ParticipantRole to DialogRole
        if participant.role.value == "initiator":
            return DialogRole.USER_1
        else:
            return DialogRole.USER_2

    async def _validate_pending_expectation(
        self,
        session: DialogSession,
        sender_role: DialogRole
    ) -> bool:
        """Validate if message from sender is expected based on session state."""
        if not session.pending_for:
            return True  # No specific expectation

        # Map DialogRole to PendingTarget
        if session.pending_for == PendingTarget.USER1 and sender_role == DialogRole.USER_1:
            return True
        elif session.pending_for == PendingTarget.USER2 and sender_role == DialogRole.USER_2:
            return True
        elif session.pending_for == PendingTarget.BOTH:
            return True

        return False

    # Backward compatibility methods for existing handlers
    async def process_user_message(
        self,
        session_id: str,
        participant_id: str,
        telegram_message_id: int,
        content: str
    ) -> Optional[List[OutboundMessage]]:
        """
        Legacy API for backward compatibility.
        Processes message and returns outbound messages for delivery.
        """
        result = await self.resume_user_message(session_id, participant_id, telegram_message_id, content)
        return result.outbox if result else None

    async def get_session_messages(self, session_id: str) -> List[SessionMessage]:
        """Get all messages for a session."""
        return await self.session_repo.get_session_messages(session_id)

    # Outbox management (integrated from OutboxService)
    async def get_delivery_targets(
        self,
        session_id: str,
        target: PendingTarget
    ) -> List[Participant]:
        """Get participant list based on target specification."""
        try:
            all_participants = await self.session_repo.get_session_participants(session_id)

            if target == PendingTarget.NONE:
                return []
            elif target == PendingTarget.BOTH:
                return all_participants
            elif target == PendingTarget.USER1:
                return [p for p in all_participants if p.role.value == "initiator"]
            elif target == PendingTarget.USER2:
                return [p for p in all_participants if p.role.value == "invitee"]

            return []

        except Exception as e:
            logger.error(f"Error resolving delivery targets for session {session_id}: {e}")
            return []

    # Graph checkpoint management (integrated from CheckpointService)
    async def save_checkpoint(
        self,
        thread_id: str,
        session_id: str,
        state_data: Dict[str, Any],
        version: int
    ) -> str:
        """Save graph state checkpoint."""
        try:
            checkpoint_id = str(uuid.uuid4())
            checkpoint = GraphCheckpoint(
                checkpoint_id=checkpoint_id,
                thread_id=thread_id,
                session_id=session_id,
                state_data=state_data,
                version=version,
                created_at=datetime.utcnow()
            )
            await self.session_repo.save_graph_checkpoint(checkpoint)
            logger.info(f"Saved checkpoint {checkpoint_id} for thread {thread_id}")
            return checkpoint_id
        except Exception as e:
            logger.error(f"Error saving checkpoint for thread {thread_id}: {e}")
            raise

    async def load_checkpoint(self, thread_id: str) -> Optional[GraphCheckpoint]:
        """Load latest checkpoint for thread."""
        try:
            return await self.session_repo.get_graph_checkpoint(thread_id)
        except Exception as e:
            logger.error(f"Error loading checkpoint for thread {thread_id}: {e}")
            return None
