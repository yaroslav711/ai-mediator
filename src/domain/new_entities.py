"""Enhanced domain entities for AI Mediator with improved database structure."""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
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


class MessageType(Enum):
    """Types of messages in the dialog."""
    USER_TEXT = "user_text"                                  # Обычное сообщение пользователя
    USER_PROFILE_DATA = "user_profile_data"                  # Ответ на анкету
    USER_CONFLICT_DESCRIPTION = "user_conflict_description"  # Описание конфликта
    AGENT_PROFILE_QUESTION = "agent_profile_question"        # AI спрашивает анкетные данные
    AGENT_CONFLICT_QUESTION = "agent_conflict_question"      # AI выясняет суть конфликта
    AGENT_CLARIFICATION = "agent_clarification"              # AI уточняющий вопрос
    AGENT_COMPROMISE_PROPOSAL = "agent_compromise_proposal"  # AI предлагает компромисс
    AGENT_SUMMARY = "agent_summary"                          # AI итоговое резюме
    SYSTEM = "system"                                        # Системные сообщения


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
    user1_id: str                          # ID первого пользователя
    user2_id: str                          # ID второго пользователя
    status: PartnershipStatus              # Статус партнерства
    created_at: datetime                   # Время создания партнерства
    last_session_at: Optional[datetime] = None  # Время последней сессии
    sessions_count: int = 0                # Количество проведенных сессий


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
    message_id: str                        # Уникальный ID сообщения
    session_id: str                        # К какой сессии относится
    sender_role: DialogRole                # Роль отправителя (USER_1/USER_2/AGENT)
    telegram_message_id: Optional[int] = None # ID сообщения в Telegram (null для AGENT)
    content: str = ""                      # Текст сообщения
    message_type: Optional[MessageType] = None  # Тип сообщения
    is_processed: bool = False             # Обработано ли AI медиатором
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
# NOTES
# ============================================================================

# Контекст для AI агента будет храниться в LangGraph State
# Дополнительные контекстные объекты здесь не нужны
 