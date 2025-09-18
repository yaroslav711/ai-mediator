"""Telegram bot handlers for AI Mediator."""
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from ...service.session_service import SessionService
from ...service.message_service import MessageService
from ...config.settings import Settings

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """Main Telegram bot handlers."""
    
    def __init__(
        self, 
        session_service: SessionService, 
        message_service: MessageService,
        settings: Settings
    ):
        self.session_service = session_service
        self.message_service = message_service
        self.bot_username = settings.telegram_bot_username

        # Validate bot username is set
        if not self.bot_username:
            raise ValueError("TELEGRAM_BOT_USERNAME must be set in environment variables")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        user_id = user.id
        username = user.username
        
        logger.info(f"Received /start from user {user_id} (@{username or 'no_username'})")
        
        # Check if this is an invite link: /start invite_code
        if context.args:
            invite_code = context.args[0]
            await self._handle_invite_join(update, invite_code, user_id, username)
        else:
            # Regular start - create new session
            await self._handle_session_creation(update, user_id, username)
    
    async def _handle_session_creation(self, update: Update, user_id: int, username: str):
        """Create new session for user."""
        try:
            session = await self.session_service.create_session(user_id, username)
            
            if session.status.value == "waiting_for_partner":
                await update.message.reply_text(
                    f"Добро пожаловать в AI Mediator!\n\n"
                    f"Сессия создана: `{session.session_id[:8]}...`\n"
                    f"Статус: Ожидаем партнера\n\n"
                    f"Чтобы пригласить партнера, используйте команду:\n"
                    f"/invite",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    f"У вас уже есть активная сессия!\n\n"
                    f"ID: `{session.session_id[:8]}...`\n"
                    f"Статус: {session.status.value}\n\n"
                    f"Используйте /invite для приглашения партнера",
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            await update.message.reply_text(
                "Ошибка создания сессии. Попробуйте еще раз."
            )
    
    async def _handle_invite_join(self, update: Update, invite_code: str, user_id: int, username: str):
        """Join session via invite code."""
        try:
            success = await self.session_service.join_session(invite_code, user_id, username)
            
            if success:
                await update.message.reply_text(
                    f"Успешно присоединились к сессии!\n\n"
                    f"Теперь вы можете писать сообщения.\n"
                    f"Ваши сообщения будут сохраняться в общем контексте диалога.\n\n"
                    f"Просто отправьте текстовое сообщение для начала диалога."
                )
            else:
                await update.message.reply_text(
                    f"Не удалось присоединиться к сессии.\n\n"
                    f"Возможные причины:\n"
                    f"• Ссылка истекла (действует 1 час)\n"
                    f"• Ссылка уже использована\n"
                    f"• Сессия уже заполнена\n"
                    f"• У вас уже есть активная сессия\n\n"
                    f"Попросите партнера создать новую ссылку командой /invite"
                )
                
        except Exception as e:
            logger.error(f"Error joining session: {e}")
            await update.message.reply_text(
                "Ошибка присоединения к сессии. Попробуйте еще раз."
            )
    
    async def invite_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /invite command - generate invite link."""
        user = update.effective_user
        user_id = user.id
        
        logger.info(f"Received /invite from user {user_id}")
        
        try:
            # Get user's active session
            session = await self.session_service.get_user_active_session(user_id)
            if not session:
                await update.message.reply_text(
                    "У вас нет активной сессии.\n\n"
                    "Используйте /start для создания новой сессии."
                )
                return
            
            # Generate invite
            invite = await self.session_service.create_invite(session.session_id, user_id)
            if not invite:
                await update.message.reply_text(
                    "Ошибка создания приглашения. Попробуйте еще раз."
                )
                return
            
            invite_url = f"https://t.me/{self.bot_username}?start={invite.invite_code}"

            # Log invite link creation for debugging
            logger.debug(f"Generated invite link: {invite_url}")

            # Create inline keyboard with button
            keyboard = [[InlineKeyboardButton("🔗 Перейти к боту", url=invite_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                f"🔗 Пригласительная ссылка создана!\n\n"
                f"Отправьте это приглашение партнеру.\n\n"
                f"Ссылка действует 1 час\n"
                f"После перехода партнер присоединится к вашей сессии",
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error creating invite: {e}")
            await update.message.reply_text(
                "Ошибка создания ссылки приглашения. Попробуйте еще раз."
            )
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages."""
        user = update.effective_user
        user_id = user.id
        message_text = update.message.text
        telegram_message_id = update.message.message_id
        
        logger.info(f"Received message from user {user_id}: {message_text[:50]}...")
        
        try:
            # Check if user has active session
            session = await self.session_service.get_user_active_session(user_id)
            if not session:
                await update.message.reply_text(
                    "У вас нет активной сессии.\n\n"
                    "Используйте /start для создания новой сессии или "
                    "перейдите по ссылке-приглашению от партнера."
                )
                return
            
            # Get user's participant info
            participant = await self.session_service.session_repo.get_participant_by_telegram_id(
                session.session_id, user_id
            )
            if not participant:
                await update.message.reply_text(
                    "Ошибка: не удалось найти информацию об участнике."
                )
                return
            
            # Process message through AI agent
            agent_response = await self.message_service.process_user_message(
                session.session_id,
                participant.participant_id,
                telegram_message_id,
                message_text
            )
            
            if agent_response:
                # Send AI response to user
                response_text = (
                    f"🤖 **AI Медиатор:**\n{agent_response.message_to_user}\n\n"
                    f"📊 **Анализ сессии:**\n{agent_response.session_recommendations or 'Нет дополнительных рекомендаций'}\n\n"
                    f"📋 **Сессия:** `{session.session_id[:8]}...`"
                )
                
                # Check if session should be ended
                if agent_response.should_end_session:
                    response_text += "\n\n⚠️ **Рекомендация:** Рассмотрите возможность завершения сессии."
                
                await update.message.reply_text(
                    response_text,
                    parse_mode='Markdown'
                )
                
                # If there's a message for partner, handle it here
                # TODO: Implement partner notification when both users are online
                if agent_response.message_to_partner:
                    logger.info(f"Message for partner in session {session.session_id}: {agent_response.message_to_partner}")
                
            else:
                # Fallback if agent processing failed
                await update.message.reply_text(
                    f"Сообщение получено и сохранено!\n\n"
                    f"Сессия: `{session.session_id[:8]}...`\n"
                    f"Статус: {session.status.value}\n\n"
                    f"⚠️ AI анализ временно недоступен.",
                    parse_mode='Markdown'
                )
            
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Ошибка обработки сообщения. Попробуйте еще раз."
            )
