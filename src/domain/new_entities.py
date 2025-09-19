"""Enhanced domain entities for AI Mediator with improved database structure."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid


# ============================================================================
# ENUMS - Business Logic Enumerations
# ============================================================================

class Gender(Enum):
    """User gender enumeration."""
    MALE = "male"                           # Мужской
    FEMALE = "female"                       # Женский


class ParticipantRole(Enum):
    """Participant role in dialog session."""
    INITIATOR = "initiator"  # Создатель сессии
    INVITEE = "invitee"      # Приглашенный участник


class DialogRole(Enum):
    """Participant role in dialog session."""
    USER_1 = "user_1"  # Первый пользователь (зафиксирован в partnership)
    USER_2 = "user_2"  # Второй пользователь (зафиксирован в partnership)
    AGENT = "agent"    # AI медиатор


class PartnershipStatus(Enum):
    """Partnership status enumeration."""
    PENDING = "pending"                     # Один создал сессию, второй еще не присоединился
    ACTIVE = "active"                       # Оба участвовали в сессии
    INACTIVE = "inactive"                   # Партнерство закрыто (или долго не используется)


class ConflictType(Enum):
    """Types of conflicts that can be mediated."""
    FINANCIAL = "financial"                 # Финансовые разногласия
    HOUSEHOLD = "household"                 # Бытовые вопросы
    PARENTING = "parenting"                 # Воспитание детей
    INTIMACY = "intimacy"                   # Интимность/близость
    COMMUNICATION = "communication"         # Проблемы общения
    CAREER = "career"                       # Карьера/работа
    FAMILY_RELATIONS = "family_relations"   # Отношения с родственниками
    SOCIAL = "social"                       # Социальная жизнь/друзья
    FUTURE_PLANS = "future_plans"           # Планы на будущее
    OTHER = "other"                         # Другое


class SessionStatus(Enum):
    """Enhanced session status enumeration."""
    WAITING_FOR_PARTNER = "waiting_for_partner"  # Ожидает второго участника
    COLLECTING_CONTEXT = "collecting_context"    # Собираем контекст конфликта
    ACTIVE = "active"                            # Активная медиация
    COMPLETED = "completed"                      # Диалог завершен
    EXPIRED = "expired"                          # Сессия истекла


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
    session_initiator_role: DialogRole     # Кто создал эту сессию (USER_1 или USER_2)
    conflict_type: Optional[ConflictType] = None    # Тип конфликта (определяется AI)
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
    telegram_message_id: int               # ID сообщения в Telegram
    content: str = ""                      # Текст сообщения
    timestamp: datetime = field(default_factory=datetime.utcnow) # Время отправки


@dataclass
class InviteLink:
    """Enhanced invitation link for joining mediation session."""
    invite_code: str                       # Уникальный код приглашения
    session_id: str                        # К какой сессии приглашение
    created_by_user_id: str                # ID пользователя-создателя (всегда user1_id)
    created_at: datetime                   # Время создания
    expires_at: datetime                   # Время истечения ссылки
    is_used: bool = False                  # Использована ли ссылка
    used_by_user_id: Optional[str] = None  # ID того, кто использовал ссылку (всегда user2_id)
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
    conflict_type: Optional[ConflictType] = None    # Определенный тип конфликта
    session_status: Optional[SessionStatus] = None  # Текущий статус сессии
    
    def to_dict(self) -> Dict[str, Any]:
        """Простая сериализация для LangGraph."""
        from dataclasses import asdict
        
        result = asdict(self)
        
        # Конвертируем enum'ы в строки (иначе LangGraph не сможет сериализовать)
        if self.conflict_type:
            result['conflict_type'] = self.conflict_type.value
        if self.session_status:
            result['session_status'] = self.session_status.value
            
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationContext':
        """Простая десериализация из LangGraph state."""
        # Восстанавливаем Message объекты
        current_message = Message(**data['current_message'])
        conversation_history = [Message(**msg) for msg in data['conversation_history']]
        
        # Восстанавливаем enum'ы
        conflict_type = ConflictType(data['conflict_type']) if data.get('conflict_type') else None
        session_status = SessionStatus(data['session_status']) if data.get('session_status') else None
        
        return cls(
            session_id=data['session_id'],
            current_message=current_message,
            conversation_history=conversation_history,
            conflict_type=conflict_type,
            session_status=session_status
        )
 