"""Main application entry point."""
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from .config.settings import get_settings
from .transport.telegram.handlers import TelegramHandlers
from .service.session_service import SessionService
from .repository.mock_repository import MockSessionRepository

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the AI Mediator bot."""
    # Load configuration
    settings = get_settings()
    
    logger.info(f"Starting bot @{settings.telegram_bot_username}")
    logger.info(f"Database URL: {settings.database_url}")
    
    # Dependency injection setup
    logger.info("Setting up dependencies...")
    session_repository = MockSessionRepository()
    session_service = SessionService(session_repository)
    telegram_handlers = TelegramHandlers(session_service, settings)
    
    # Bot setup
    app = Application.builder().token(settings.telegram_bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", telegram_handlers.start_command))
    app.add_handler(CommandHandler("invite", telegram_handlers.invite_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, telegram_handlers.handle_message))
    
    logger.info("🤖 Bot is starting with session management...")
    logger.info("📋 Available commands:")
    logger.info("   /start - Create new session or join via invite")
    logger.info("   /invite - Generate invitation link")
    logger.info("   <text> - Send message to session context")
    
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
