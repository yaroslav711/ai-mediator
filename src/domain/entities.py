"""Domain entities for AI Mediator dialog mechanism."""
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
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


@dataclass
class DialogSession:
    """Dialog session between two users."""
    session_id: str
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None


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
    telegram_message_id: int                 # ID сообщения в Telegram
    content: str                            # Текст сообщения
    timestamp: datetime                     # Время отправки
    is_processed: bool = False              # Обработано ли AI медиатором


@dataclass
class InviteLink:
    """Invitation link for joining dialog session."""
    invite_code: str                        # Уникальный код приглашения
    session_id: str                         # К какой сессии приглашение
    created_by: str                         # participant_id создателя
    created_at: datetime
    expires_at: datetime                    # Время истечения ссылки
    is_used: bool = False                   # Использована ли ссылка
