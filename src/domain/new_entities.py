"""Enhanced domain entities for AI Mediator with improved database structure."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid
import cattrs


# ============================================================================
# ENUMS - Business Logic Enumerations
# ============================================================================

class Gender(Enum):
    """User gender enumeration."""
    MALE = "male"                           # Мужской
    FEMALE = "female"                       # Женский


class DialogRole(Enum):
    """Participant role in dialog session."""
    USER_1 = "user_1"  # Первый пользователь (зафиксирован в partnership)
    USER_2 = "user_2"  # Второй пользователь (зафиксирован в partnership)
    AGENT = "agent"    # AI медиатор


class MessageType(Enum):
    USER_TEXT = "user_text"
    USER_QUESTIONNAIRE = "user_questionnaire"  
    AGENT_TEXT = "agent_text"
    AGENT_QUSTIONNAIRE = "agent_questionnaire"
    SYSTEM = "system"


class PartnershipStatus(Enum):
    """Partnership status enumeration."""
    PENDING = "pending"                     # Один создал сессию, второй еще не присоединился
    ACTIVE = "active"                       # Оба участвовали в сессии
    INACTIVE = "inactive"                   # Партнерство закрыто (или долго не используется)


class SessionStatus(Enum):
    """Enhanced session status enumeration."""
    WAITING_FOR_PARTNER = "waiting_for_partner"  # Ожидает второго участника
    COLLECTING_CONTEXT = "collecting_context"    # Собираем контекст конфликта
    ACTIVE = "active"                            # Активная медиация
    COMPLETED = "completed"                      # Диалог завершен
    EXPIRED = "expired"                          # Сессия истекла


# ============================================================================
# DOMAIN ENTITIES - Core Business Objects
# ============================================================================

@dataclass
class User:
    """User entity with profile information."""
    user_id: str                            # Уникальный ID пользователя
    telegram_user_id: int                   # ID пользователя в Telegram
    telegram_username: Optional[str]        # Username в Telegram (может отсутствовать)
    name: Optional[str] = None              # Имя из анкеты
    age: Optional[int] = None               # Возраст из анкеты
    gender: Optional[Gender] = None         # Пол из анкеты
    profile_completed: bool = False         # Заполнена ли анкета
    created_at: datetime = field(default_factory=datetime.utcnow) # Время регистрации
    updated_at: datetime = field(default_factory=datetime.utcnow) # Время последнего обновления


@dataclass
class Partnership:
    """Long-term partnership between two users with fixed roles."""
    partnership_id: str                    # Уникальный ID партнерства
    user1_id: str                          # ID первого пользователя (кто первый создал связку)
    user2_id: str                          # ID второго пользователя (кто присоединился)
    status: PartnershipStatus              # Статус партнерства
    created_at: datetime                   # Время создания партнерства


@dataclass
class MediationSession:
    """Mediation session between partners."""
    session_id: str                        # Уникальный ID сессии
    partnership_id: str                    # ID партнерства
    session_initiator_role: DialogRole     # Кто инициировал эту сессию (USER_1 или USER_2)
    status: SessionStatus                  # Статус сессии
    created_at: datetime                   # Время создания
    updated_at: datetime                   # Время последнего обновления
    expires_at: Optional[datetime] = None  # Время истечения (для автозакрытия)
    completed_at: Optional[datetime] = None # Время завершения


@dataclass
class Message:
    """Message within a mediation session."""
    message_id: int                        # Монотонно возрастающий ID
    session_id: str                        # К какой сессии относится
    sender_role: DialogRole                # Роль отправителя (USER_1/USER_2/AGENT)
    telegram_message_id: Optional[int] = None  # ID сообщения в Telegram
    message_type: Optional[MessageType] = None # Тип сообщения
    content: str = ""                      # Текст сообщения
    timestamp: datetime = field(default_factory=datetime.utcnow) # Время отправки


@dataclass
class InviteLink:
    """Enhanced invitation link for joining mediation session."""
    invite_code: str                       # Уникальный код приглашения
    session_id: str                        # К какой сессии приглашение
    created_by_user_id: str                # ID пользователя-создателя (всегда USER_1)
    created_at: datetime                   # Время создания
    expires_at: datetime                   # Время истечения ссылки
    is_used: bool = False                  # Использована ли ссылка
    used_by_user_id: Optional[str] = None  # ID того, кто использовал ссылку (всегда USER_2)
    used_at: Optional[datetime] = None     # Время использования


# ============================================================================
# LANGGRAPH STATE STRUCTURES
# ============================================================================

# Работа с LangGraph:
# 1. Загрузка: context.to_dict() → передаем в LangGraph
# 2. Сохранение: ConversationContext.from_dict(state) → восстанавливаем из LangGraph

@dataclass
class ConversationContext:
    """Context for LangGraph agent processing and state management."""
    session_id: str                        # ID сессии
    current_message: Message               # Текущее обрабатываемое сообщение
    conversation_history: List[Message]    # История всех сообщений в сессии
    
    # Опциональные поля (можно добавлять по мере надобности)
    session_status: Optional[SessionStatus] = None  # Текущий статус сессии
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for LangGraph state."""
        converter = cattrs.Converter()
        converter.register_unstructure_hook(datetime, lambda dt: dt.isoformat())
        return converter.unstructure(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Deserialize from LangGraph state dict."""
        converter = cattrs.Converter()
        converter.register_structure_hook(datetime, lambda ts, _: 
            datetime.fromisoformat(ts) if isinstance(ts, str) else ts)
        return converter.structure(data, cls)
 