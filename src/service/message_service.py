"""Message processing service with AI agent integration."""
import logging
from datetime import datetime
from typing import Optional, List
import uuid

from ..domain.entities import SessionMessage, DialogSession
from ..repository.interface import SessionRepositoryInterface
from ..external_services.agent.interface import AgentInterface, ConversationContext, AgentResponse

logger = logging.getLogger(__name__)


class MessageService:
    """Service for processing messages through AI agent."""
    
    def __init__(
        self, 
        session_repo: SessionRepositoryInterface,
        agent: AgentInterface
    ):
        self.session_repo = session_repo
        self.agent = agent
    
    async def process_user_message(
        self,
        session_id: str,
        participant_id: str,
        telegram_message_id: int,
        content: str
    ) -> Optional[AgentResponse]:
        """
        Process user message through AI agent.
        
        Args:
            session_id: Session ID
            participant_id: ID of message sender
            telegram_message_id: Telegram message ID
            content: Message text content
            
        Returns:
            AgentResponse with AI recommendations, or None if processing failed
        """
        try:
            # 1. Save incoming message
            message = await self._save_message(
                session_id, participant_id, telegram_message_id, content
            )
            if not message:
                logger.error(f"Failed to save message for session {session_id}")
                return None
            
            # 2. Get conversation context
            context = await self._build_conversation_context(session_id, message)
            if not context:
                logger.error(f"Failed to build context for session {session_id}")
                return None
            
            # 3. Process through AI agent
            agent_response = await self.agent.process_message(context)
            
            # 4. Save agent response if needed
            if agent_response.session_recommendations:
                await self._log_agent_insights(session_id, agent_response)
            
            # 5. Mark message as processed
            await self.session_repo.mark_message_processed(message.message_id)
            
            logger.info(f"Successfully processed message {message.message_id} for session {session_id}")
            return agent_response
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            return None
    
    async def get_session_messages(self, session_id: str) -> List[SessionMessage]:
        """Get all messages for a session."""
        return await self.session_repo.get_session_messages(session_id)
    
    async def _save_message(
        self,
        session_id: str,
        participant_id: str,
        telegram_message_id: int,
        content: str
    ) -> Optional[SessionMessage]:
        """Save message to repository."""
        message = SessionMessage(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            participant_id=participant_id,
            telegram_message_id=telegram_message_id,
            content=content,
            timestamp=datetime.utcnow(),
            is_processed=False
        )
        
        success = await self.session_repo.save_message(message)
        return message if success else None
    
    async def _build_conversation_context(
        self, 
        session_id: str, 
        current_message: SessionMessage
    ) -> Optional[ConversationContext]:
        """Build conversation context for agent processing."""
        try:
            # Get conversation history
            history = await self.session_repo.get_session_messages(session_id)
            
            # Get participants count
            participants = await self.session_repo.get_session_participants(session_id)
            
            return ConversationContext(
                session_id=session_id,
                current_message=current_message,
                conversation_history=history,
                participants_count=len(participants)
            )
            
        except Exception as e:
            logger.error(f"Error building conversation context: {e}")
            return None
    
    async def _log_agent_insights(self, session_id: str, response: AgentResponse):
        """Log agent insights and recommendations."""
        # TODO: Implement proper logging/storage of agent insights
        # This could be stored in a separate table for analytics
        logger.info(
            f"Agent insights for session {session_id}: "
            f"recommendations={response.session_recommendations}, "
            f"should_end={response.should_end_session}"
        )
