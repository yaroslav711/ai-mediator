"""Tests for Telegram handlers."""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from telegram import Update, User, Message, Chat
from telegram.ext import ContextTypes

from internal.transport.telegram.handlers import TelegramHandlers
from internal.service.session_service import SessionService
from internal.config.settings import Settings
from internal.domain.entities import DialogSession, SessionStatus


@pytest.fixture
def mock_session_service():
    """Mock session service."""
    return AsyncMock(spec=SessionService)


@pytest.fixture
def mock_settings():
    """Mock settings."""
    settings = MagicMock(spec=Settings)
    settings.telegram_bot_username = "test_bot"
    return settings


@pytest.fixture
def telegram_handlers(mock_session_service, mock_settings):
    """Create TelegramHandlers instance with mocked dependencies."""
    return TelegramHandlers(mock_session_service, mock_settings)


@pytest.fixture
def mock_update():
    """Create mock Telegram update."""
    update = MagicMock(spec=Update)
    user = MagicMock(spec=User)
    user.id = 12345
    user.username = "testuser"

    message = MagicMock(spec=Message)
    message.reply_text = AsyncMock()

    update.effective_user = user
    update.message = message

    return update


@pytest.fixture
def mock_context():
    """Create mock Telegram context."""
    context = MagicMock(spec=ContextTypes.DEFAULT_TYPE)
    context.args = []
    return context


@pytest.mark.asyncio
async def test_start_command_creates_new_session_successfully(
    telegram_handlers, mock_update, mock_context, mock_session_service
):
    """Test that /start command successfully creates a new session."""
    # Arrange
    session_id = "test-session-123"
    mock_session = DialogSession(
        session_id=session_id,
        status=SessionStatus.WAITING_FOR_PARTNER,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    mock_session_service.create_session.return_value = mock_session

    # Act
    await telegram_handlers.start_command(mock_update, mock_context)

    # Assert
    mock_session_service.create_session.assert_called_once_with(12345, "testuser")
    mock_update.message.reply_text.assert_called_once()

    # Verify the response message contains expected content
    call_args = mock_update.message.reply_text.call_args
    response_text = call_args[0][0]

    assert "Добро пожаловать в AI Mediator!" in response_text
    assert "Сессия создана:" in response_text
    assert "Ожидаем партнера" in response_text
    assert "/invite" in response_text
    assert call_args[1]["parse_mode"] == "Markdown"