"""Telegram bot handlers for AI Mediator."""
import logging
from typing import List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from service.session_service import SessionService
from service.message_service import MessageService
from config.settings import Settings
from domain.entities import OutboundMessage, PendingTarget

logger = logging.getLogger(__name__)


class TelegramHandlers:
    """Main Telegram bot handlers."""
    
    def __init__(
        self,
        session_service: SessionService,
        message_service: MessageService,
        settings: Settings,
        bot=None
    ):
        self.session_service = session_service
        self.message_service = message_service
        self.bot_username = settings.telegram_bot_username
        self.bot = bot  # Store bot instance for sending messages

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
                # Get session to start mediation
                session = await self.session_service.get_user_active_session(user_id)
                if session and session.status.value == "active":
                    # Get all participants for starting mediation
                    participants = await self.session_service.session_repo.get_session_participants(session.session_id)
                    participant_ids = [p.participant_id for p in participants]

                    # Start mediation automatically
                    logger.info(f"Auto-starting mediation for session {session.session_id}")
                    result = await self.message_service.start_mediation_session(
                        session.session_id,
                        participant_ids
                    )

                    # Deliver initial outbound messages
                    if result and result.outbox:
                        await self._deliver_outbound_messages(session.session_id, result.outbox)

                await update.message.reply_text(
                    f"✅ Успешно присоединились к сессии!\n\n"
                    f"🤖 AI Медиатор автоматически начал работу.\n"
                    f"Следуйте инструкциям медиатора для разрешения конфликта.\n\n"
                    f"Просто отправляйте текстовые сообщения - медиатор будет направлять диалог."
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

            # Process message through LangGraph agent
            result = await self.message_service.resume_user_message(
                session.session_id,
                participant.participant_id,
                telegram_message_id,
                message_text
            )

            if result:
                # Deliver outbound messages from agent
                if result.outbox:
                    await self._deliver_outbound_messages(session.session_id, result.outbox)

                # Send status update to sender
                status_msg = f"✅ Сообщение обработано медиатором"
                if result.phase:
                    status_msg += f"\n📍 Фаза: {result.phase.value}"
                if result.pending_for:
                    status_msg += f"\n⏳ Ожидаем: {result.pending_for.value}"

                await update.message.reply_text(status_msg)

            else:
                # Message was not processed (e.g., wrong turn, duplicate, etc.)
                await update.message.reply_text(
                    f"📝 Сообщение сохранено.\n\n"
                    f"Возможно, сейчас не ваша очередь говорить или "
                    f"сообщение уже было обработано."
                )

            # Check for pending outbound messages and deliver them
            await self._check_and_deliver_pending_messages(session.session_id)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(
                "Ошибка обработки сообщения. Попробуйте еще раз."
            )

    async def _deliver_outbound_messages(self, session_id: str, outbox: List[OutboundMessage]):
        """Deliver outbound messages to target participants."""
        try:
            for message in outbox:
                # Get target participants
                targets = await self.message_service.get_delivery_targets(session_id, message.target)

                delivery_results = {}

                for participant in targets:
                    try:
                        # Send message to telegram user
                        telegram_message = await self._send_message_to_user(
                            participant.telegram_user_id,
                            f"🤖 **AI Медиатор:**\n\n{message.content}",
                            parse_mode='Markdown'
                        )

                        if telegram_message:
                            delivery_results[participant.participant_id] = telegram_message.message_id
                            logger.info(f"Delivered message {message.message_id[:8]}... to user {participant.telegram_user_id}")

                    except Exception as e:
                        logger.error(f"Failed to deliver message to user {participant.telegram_user_id}: {e}")

                # Mark message as delivered
                if delivery_results:
                    await self.message_service.mark_outbound_delivered(message.message_id, delivery_results)

        except Exception as e:
            logger.error(f"Error delivering outbound messages: {e}")

    async def _check_and_deliver_pending_messages(self, session_id: str):
        """Check for pending outbound messages and deliver them."""
        try:
            pending_messages = await self.message_service.get_pending_outbound_messages(session_id)
            if pending_messages:
                logger.info(f"Found {len(pending_messages)} pending messages for session {session_id}")
                await self._deliver_outbound_messages(session_id, pending_messages)
        except Exception as e:
            logger.error(f"Error checking pending messages: {e}")

    async def _send_message_to_user(self, telegram_user_id: int, text: str, **kwargs):
        """Send message to specific telegram user."""
        try:
            if self.bot:
                # Use actual bot instance to send message
                message = await self.bot.send_message(
                    chat_id=telegram_user_id,
                    text=text,
                    **kwargs
                )
                logger.info(f"Sent message to user {telegram_user_id}: {text[:50]}...")
                return message
            else:
                # Fallback when bot instance is not available
                logger.warning(f"Bot instance not available, mocking message to user {telegram_user_id}")

                class MockMessage:
                    def __init__(self):
                        self.message_id = 12345

                return MockMessage()

        except Exception as e:
            logger.error(f"Error sending message to user {telegram_user_id}: {e}")
            return None
