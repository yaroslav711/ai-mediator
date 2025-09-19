"""LangGraph-based AI Agent implementation."""
import logging
from typing import List
from datetime import datetime
import uuid

from external_services.agent.interface import AgentInterface, AgentResult
from domain.entities import OutboundMessage, PendingTarget, GraphPhase, SessionMessage, DialogRole

logger = logging.getLogger(__name__)


class LangGraphAgent(AgentInterface):
    """AI Mediator agent implementation using LangGraph."""

    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.7):
        """
        Initialize LangGraph agent.

        Args:
            model_name: LLM model to use
            temperature: Model temperature for responses
        """
        self.model_name = model_name
        self.temperature = temperature

        # TODO: Initialize LangGraph components
        # self.graph = self._build_agent_graph()
        # self.checkpointer = MemorySaver()  # or PostgresCheckpointer
        logger.info(f"LangGraph agent initialized with model: {model_name}")

    async def start_session(self, thread_id: str, participants: List[str]) -> AgentResult:
        """
        Start new mediation session.

        Args:
            thread_id: Unique thread identifier for LangGraph
            participants: List of participant IDs

        Returns:
            AgentResult with initial outbox and status
        """
        logger.info(f"Starting session for thread {thread_id} with participants: {participants}")

        # TODO: Replace with actual LangGraph invocation
        # config = {"configurable": {"thread_id": thread_id}}
        # result = await self.graph.ainvoke(
        #     {"participants": participants, "phase": "start"},
        #     config=config
        # )

        # Mock initial response
        initial_message = OutboundMessage(
            message_id=str(uuid.uuid4()),
            session_id=thread_id,  # Using thread_id as session_id for now
            target=PendingTarget.USER1,
            content="Добро пожаловать в сессию медиации! Пожалуйста, опишите ситуацию со своей стороны.",
            created_at=datetime.utcnow()
        )

        return AgentResult(
            outbox=[initial_message],
            status="waiting",
            phase=GraphPhase.GATHER_USER1_PERSPECTIVE,
            pending_for=PendingTarget.USER1,
            state_snapshot={"phase": "gather_u1", "participants": participants}
        )

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
        logger.info(f"Resuming session {thread_id} with input from {sender} (role: {sender_role}) in phase {current_phase}: {message_text[:50]}...")

        # TODO: Replace with actual LangGraph invocation
        # config = {"configurable": {"thread_id": thread_id}}
        # result = await self.graph.ainvoke(
        #     {"sender": sender, "message": message_text, "phase": current_phase},
        #     config=config
        # )

        # Mock response based on current phase and sender
        if current_phase == GraphPhase.GATHER_USER1_PERSPECTIVE and sender_role == "user_1":
            # USER1 provided their perspective, now ask USER2
            response_message = OutboundMessage(
                message_id=str(uuid.uuid4()),
                session_id=thread_id,
                target=PendingTarget.USER2,
                content="Теперь ваша очередь! Пожалуйста, расскажите о ситуации со своей стороны.",
                created_at=datetime.utcnow()
            )
            next_phase = GraphPhase.GATHER_USER2_PERSPECTIVE
            pending_for = PendingTarget.USER2

        elif current_phase == GraphPhase.GATHER_USER2_PERSPECTIVE and sender_role == "user_2":
            # USER2 provided their perspective, now analyze conflict
            response_message = OutboundMessage(
                message_id=str(uuid.uuid4()),
                session_id=thread_id,
                target=PendingTarget.BOTH,
                content="Спасибо за ваши ответы. Теперь я проанализирую ситуацию и предложу варианты решения.",
                created_at=datetime.utcnow()
            )
            next_phase = GraphPhase.ANALYZE_CONFLICT
            pending_for = PendingTarget.NONE

        else:
            # Default fallback - should not happen in correct flow
            logger.warning(f"Unexpected phase/sender combination: phase={current_phase}, sender_role={sender_role}")
            response_message = OutboundMessage(
                message_id=str(uuid.uuid4()),
                session_id=thread_id,
                target=PendingTarget.BOTH,
                content="Сообщение получено. Медиатор анализирует ситуацию.",
                created_at=datetime.utcnow()
            )
            next_phase = current_phase or GraphPhase.ANALYZE_CONFLICT
            pending_for = PendingTarget.NONE

        return AgentResult(
            outbox=[response_message],
            status="waiting",
            phase=next_phase,
            pending_for=pending_for,
            state_snapshot={"phase": next_phase.value, "last_input": message_text, "sender": sender}
        )
    
    async def health_check(self) -> bool:
        """Check if LangGraph agent is ready."""
        # TODO: Add actual health checks for LangGraph components
        logger.debug("LangGraph agent health check")
        return True
    
    def _build_agent_graph(self):
        """
        Build LangGraph agent workflow.
        
        This method will contain the actual LangGraph graph definition:
        1. Message analysis node
        2. Context understanding node  
        3. Mediation strategy selection node
        4. Response generation node
        5. Recommendation formulation node
        """
        # TODO: Implement LangGraph graph
        pass
    
    def _format_conversation_history(self, history: List[SessionMessage]) -> str:
        """Format conversation history for LLM input."""
        # TODO: Implement proper formatting
        return f"Conversation with {len(history)} messages"
    
    def _extract_insights(self, llm_response: str) -> dict:
        """Extract structured insights from LLM response."""
        # TODO: Implement insight extraction
        return {"mood": "neutral", "conflict_level": "low"}
