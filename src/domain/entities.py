"""Domain entities for AI Mediator dialog mechanism."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Literal
import uuid


class SessionStatus(Enum):
    """Session status enumeration."""
    WAITING_FOR_PARTNER = "waiting_for_partner"  # Ожидает второго участника
    ACTIVE = "active"                           # Оба участника подключены
    COMPLETED = "completed"                     # Диалог завершен
    EXPIRED = "expired"                         # Сессия истекла


class ParticipantRole(Enum):
    """Participant role in dialog session."""
    INITIATOR = "initiator"  # Создатель сессии
    INVITEE = "invitee"     # Приглашенный участник


class DialogRole(Enum):
    """Participant role in dialog session."""
    USER_1 = "user_1"  # Создатель сессии
    USER_2 = "user_2"     # Приглашенный участник
    MEDIATOR = "mediator"  # AI медиатор


class GraphPhase(Enum):
    """LangGraph mediation phases."""
    GATHER_USER1_PERSPECTIVE = "gather_u1"
    GATHER_USER2_PERSPECTIVE = "gather_u2"
    ANALYZE_CONFLICT = "analyze"
    GENERATE_OPTIONS = "options"
    FACILITATE_AGREEMENT = "agreement"
    FINALIZE = "finalize"
    DONE = "done"


class PendingTarget(Enum):
    """Who the graph is waiting for."""
    USER1 = "user1"
    USER2 = "user2"
    BOTH = "both"
    NONE = "none"


@dataclass
class DialogSession:
    """Dialog session between two users."""
    session_id: str
    status: Optional[SessionStatus]  # Allow None for initialization
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    thread_id: Optional[str] = None
    phase: Optional[GraphPhase] = None
    pending_for: Optional[PendingTarget] = None
    graph_state_version: int = 0


@dataclass
class Participant:
    """Session participant."""
    participant_id: str
    session_id: str
    telegram_user_id: int                    # ID пользователя в Telegram
    telegram_username: Optional[str]         # Username в Telegram (может отсутствовать)
    role: ParticipantRole
    joined_at: datetime
    is_active: bool = True


@dataclass
class SessionMessage:
    """Message within a dialog session."""
    message_id: str
    session_id: str                          # К какой сессии относится
    participant_id: str                      # Кто отправил
    role: DialogRole                        # Роль участника
    telegram_message_id: Optional[int] = None  # ID сообщения в Telegram (None для исходящих)
    content: str = ""                       # Текст сообщения
    timestamp: Optional[datetime] = None    # Время отправки
    is_processed: bool = False              # Обработано ли AI медиатором
    target: Optional[PendingTarget] = None  # Адресат сообщения (для исходящих)
    phase_snapshot: Optional[GraphPhase] = None  # Фаза графа на момент сообщения


@dataclass
class ConversationContext:
    """Context for agent processing."""
    session_id: str
    current_message: SessionMessage
    conversation_history: List[SessionMessage]
    participants_count: int


@dataclass
class OutboundMessage:
    """Outbound message for targeted delivery."""
    message_id: str
    session_id: str
    target: PendingTarget                   # Кому доставить
    content: str                           # Текст сообщения
    created_at: datetime
    delivered_at: Optional[datetime] = None
    telegram_message_ids: Optional[Dict[str, int]] = None  # {participant_id: telegram_message_id}


@dataclass
class GraphCheckpoint:
    """Graph state checkpoint for LangGraph."""
    checkpoint_id: str
    thread_id: str
    session_id: str
    state_data: Dict[str, Any]             # Serialized graph state
    version: int
    created_at: datetime


@dataclass
class InviteLink:
    """Invitation link for joining dialog session."""
    invite_code: str                        # Уникальный код приглашения
    session_id: str                         # К какой сессии приглашение
    created_by: str                         # participant_id создателя
    created_at: datetime
    expires_at: datetime                    # Время истечения ссылки
    is_used: bool = False                   # Использована ли ссылка
