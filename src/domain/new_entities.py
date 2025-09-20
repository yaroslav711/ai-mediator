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

class DialogRole(Enum):
    """Participant role in dialog session."""
    USER_1 = "user_1"  # Первый пользователь (зафиксирован в partnership)
    USER_2 = "user_2"  # Второй пользователь (зафиксирован в partnership)
    AGENT = "agent"    # AI медиатор


class MessageType(Enum):
    """Message type enumeration for different processing logic."""
    USER_MESSAGE = "user_message"           # Сообщение от пользователя
    AGENT_MESSAGE = "agent_message"         # Сообщение от AI медиатора
    AGENT_FINAL = "agent_final"             # Предложение завершить сессию (с кнопкой в Telegram)
    SYSTEM = "system"                       # Системные уведомления вне сессии (построение пары, ...)


class PartnershipStatus(Enum):
    """Partnership status enumeration."""
    ACTIVE = "active"                       # Партнерство активно, можно создавать сессии
    CLOSED = "closed"                       # Партнерство закрыто, новые сессии не создаются


class SessionStatus(Enum):
    """Session status enumeration."""
    ACTIVE = "active"                            # Активная медиация
    COMPLETED = "completed"                      # Диалог завершен
    EXPIRED = "expired"                          # Сессия истекла


# ============================================================================
# DOMAIN ENTITIES - Core Business Objects
# ============================================================================

@dataclass
class User:
    """User entity with basic profile information.
    
    СОЗДАНИЕ:
    - Создается при первом взаимодействии пользователя с Telegram ботом
    - user_id генерируется как UUID, telegram_user_id берется из Telegram API
    
    ИСПОЛЬЗОВАНИЕ:
    - Базовая сущность для идентификации пользователей в системе
    - user_id используется во всех других сущностях как foreign key
    - Профиль остается простым - только данные из Telegram
    
    ЖИЗНЕННЫЙ ЦИКЛ:
    - Создается один раз при регистрации
    - Не может обновляться
    """
    user_id: str                            # Уникальный ID пользователя
    telegram_user_id: int                   # ID пользователя в Telegram
    telegram_username: Optional[str]        # Username в Telegram (может отсутствовать)
    created_at: datetime = field(default_factory=datetime.utcnow) # Время регистрации
    updated_at: datetime = field(default_factory=datetime.utcnow) # Время последнего обновления


@dataclass
class Partnership:
    """Long-term partnership between two users with fixed roles.
    
    СОЗДАНИЕ:
    - Создается автоматически при успешном переходе user_2 по пригласительной ссылке
    - Определяет фиксированные роли: user1_id (создатель) и user2_id (присоединившийся)
    - Создается сразу со статусом ACTIVE
    
    ИСПОЛЬЗОВАНИЕ:
    - Основа для создания медиационных сессий между партнерами
    - Сохраняет порядок ролей: USER_1 и USER_2 всегда соответствуют user1_id и user2_id
    - Позволяет отслеживать историю взаимодействий между конкретными пользователями
    - Может быть закрыта (CLOSED) пользователем или системой
    
    ЖИЗНЕННЫЙ ЦИКЛ:
    - ACTIVE: партнерство активно, можно создавать новые сессии
    - CLOSED: партнерство закрыто, новые сессии не создаются
    """
    partnership_id: str                    # Уникальный ID партнерства
    user1_id: str                          # ID первого пользователя (кто первый создал связку)
    user2_id: str                          # ID второго пользователя (кто присоединился)
    status: PartnershipStatus              # Статус партнерства
    created_at: datetime                   # Время создания партнерства


@dataclass
class MediationSession:
    """Mediation session between partners.
    
    СОЗДАНИЕ:
    - Создается ТОЛЬКО при первом сообщении любого пользователя из Partnership
    - session_initiator_role определяет, кто начал текущую сессию
    - Изначально статус ACTIVE
    
    ИСПОЛЬЗОВАНИЕ:
    - Контейнер для всех сообщений и состояния медиационного процесса
    - Хранит полное состояние LangGraph в поле langgraph_state
    - Живет 24 часа с момента создания (expires_at)
    - При входящем сообщении проверяется наличие ACTIVE сессии (если есть - продолжается сессия)
    - Если нет ACTIVE сессии - создается новая с первым сообщением в langgraph_state
    - Может быть закрыта досрочно командой в Telegram боте
    
    ЖИЗНЕННЫЙ ЦИКЛ:
    - ACTIVE: идет активная медиация (начальный статус)
    - COMPLETED: сессия завершена успешно
    - EXPIRED: сессия истекла по времени (24 часа)
    
    LANGGRAPH STATE:
    - langgraph_state хранит полное состояние AI агента
    - Обновляется при каждом сообщении в рамках сессии
    - При создании новой сессии уже содержит первое сообщение
    - Позволяет сохранять промежуточные состояния для human-in-the-loop
    
    ЛОГИКА СОЗДАНИЯ:
    1. Поступает первое сообщение → создается Message
    2. Создается MediationSession с langgraph_state, содержащим этот Message
    3. Последующие сообщения обновляют существующий langgraph_state
    """
    session_id: str                        # Уникальный ID сессии
    partnership_id: str                    # ID партнерства
    session_initiator_role: DialogRole     # Кто инициировал эту сессию (USER_1 или USER_2)
    status: SessionStatus                  # Статус сессии
    created_at: datetime                   # Время создания
    updated_at: datetime                   # Время последнего обновления
    expires_at: Optional[datetime] = None  # Время истечения (для автозакрытия)
    completed_at: Optional[datetime] = None # Время завершения
    # Состояние LangGraph для сохранения контекста AI агента между сообщениями
    # При создании сессии уже содержит первое сообщение, поэтому НЕ может быть None
    langgraph_state: Dict[str, Any]


@dataclass
class Message:
    """Message within a mediation session.
    
    СОЗДАНИЕ:
    - Создается при каждом сообщении от пользователя или AI агента
    - message_id автоинкрементируется в БД для сортировки
    - sender_role определяется автоматически: USER_1, USER_2 или AGENT
    - message_type определяет логику обработки сообщения на бэкенде
    - telegram_message_id связывает с конкретным сообщением в Telegram
    
    ИСПОЛЬЗОВАНИЕ:
    - Основная единица диалога в медиационной сессии
    - Используется для формирования истории диалога в LangGraph состоянии
    - Позволяет восстановить полную историю диалога
    - Сохраняется для аналитики и улучшения AI модели
    
    ТИПЫ СООБЩЕНИЙ:
    - USER_MESSAGE: сообщение от пользователя
    - AGENT_MESSAGE: сообщение от AI медиатора в процессе диалога
    - AGENT_FINAL: предложение от агента завершить сессию (отображается с кнопкой)
    - SYSTEM: системные уведомления вне сессии (создание партнерства и т.п.)
    
    ЛОГИКА ОБРАБОТКИ MESSAGE_TYPE:
    - AGENT_FINAL может триггерить показ кнопок завершения в Telegram
    - SYSTEM сообщения не участвуют в медиационном процессе
    - USER_MESSAGE и AGENT_MESSAGE формируют основной диалог
    
    ЖИЗНЕННЫЙ ЦИКЛ:
    - Создается немедленно при получении
    - Добавляется в langgraph_state сессии для обработки AI агентом
    - Сохраняется в БД для истории
    - Остается неизменным после создания (иммутабельный)
    """
    message_id: int                        # Монотонно возрастающий ID
    session_id: str                        # К какой сессии относится
    sender_role: DialogRole                # Роль отправителя (USER_1/USER_2/AGENT)
    message_type: MessageType              # Тип сообщения для разной обработки на бэкенде
    telegram_message_id: Optional[int] = None  # ID сообщения в Telegram
    content: str = ""                      # Текст сообщения
    timestamp: datetime = field(default_factory=datetime.utcnow) # Время отправки


@dataclass
class InviteLink:
    """Invitation link for creating partnership.
    
    СОЗДАНИЕ:
    - Создается пользователем (user_1) через команду в Telegram боте
    - invite_code генерируется как уникальная строка для безопасности
    - Имеет ограниченное время жизни (expires_at)
    
    ИСПОЛЬЗОВАНИЕ:
    - Пересылается user_1 потенциальному партнеру
    - Партнер переходит по ссылке и становится user_2
    - При переходе проверяется: не истекла ли ссылка, не использована ли уже
    - После успешного перехода создается Partnership
    
    ЖИЗНЕННЫЙ ЦИКЛ:
    - Создается: при генерации пользователем через бота
    - Используется: при переходе второго пользователя (is_used=True)
    - Истекает: автоматически через заданное время или при использовании
    - Остается в системе для аудита и статистики
    """
    invite_code: str                       # Уникальный код приглашения
    created_by_user_id: str                # ID пользователя-создателя (всегда USER_1)
    created_at: datetime                   # Время создания
    expires_at: datetime                   # Время истечения ссылки
    is_used: bool = False                  # Использована ли ссылка
    used_by_user_id: Optional[str] = None  # ID того, кто использовал ссылку (всегда USER_2)
    used_at: Optional[datetime] = None     # Время использования
 