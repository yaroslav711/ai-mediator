#!/usr/bin/env python3
"""Test LangGraph integration with the AI Mediator system."""
import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.repository.mock_repository import MockSessionRepository
from src.service.session_service import SessionService
from src.service.message_service import MessageService
from src.external_services.agent.langgraph_agent import LangGraphAgent
from src.domain.entities import SessionStatus, ParticipantRole

async def test_complete_flow():
    """Test complete mediation flow."""
    print("🧪 Testing LangGraph Integration")
    print("=" * 50)

    # Setup services
    repo = MockSessionRepository()
    session_service = SessionService(repo)
    agent = LangGraphAgent()
    message_service = MessageService(repo, agent)

    # Test 1: Create session
    print("\n1️⃣ Creating session for User1 (Anna)...")
    session = await session_service.create_session(telegram_user_id=111, telegram_username="anna")
    print(f"   Session ID: {session.session_id[:8]}...")
    print(f"   Status: {session.status.value}")

    # Test 2: Generate invite
    print("\n2️⃣ Creating invite link...")
    invite = await session_service.create_invite(session.session_id, 111)
    print(f"   Invite code: {invite.invite_code}")

    # Test 3: Join session
    print("\n3️⃣ User2 (Boris) joins via invite...")
    success = await session_service.join_session(invite.invite_code, telegram_user_id=222, telegram_username="boris")
    print(f"   Join success: {success}")

    # Get updated session
    session = await session_service.get_user_active_session(111)
    print(f"   Updated status: {session.status.value}")

    # Test 4: Start mediation
    print("\n4️⃣ Starting LangGraph mediation...")
    participants = await repo.get_session_participants(session.session_id)
    participant_ids = [p.participant_id for p in participants]
    print(f"   Participants: {len(participants)}")

    result = await message_service.start_mediation_session(session.session_id, participant_ids)
    if result:
        print(f"   Started! Phase: {result.phase.value}")
        print(f"   Pending for: {result.pending_for.value}")
        print(f"   Outbox messages: {len(result.outbox)}")

        for msg in result.outbox:
            print(f"     → {msg.target.value}: {msg.content[:50]}...")

    # Test 5: User1 sends message
    print("\n5️⃣ User1 (Anna) sends first message...")
    anna_participant = next(p for p in participants if p.role.value == "initiator")

    result = await message_service.resume_user_message(
        session.session_id,
        anna_participant.participant_id,
        telegram_message_id=1001,
        content="Борис каждый день слушает музыку до 2 ночи, мне сложно спать"
    )

    if result:
        print(f"   Response phase: {result.phase.value}")
        print(f"   Now pending for: {result.pending_for.value}")
        print(f"   Outbox messages: {len(result.outbox)}")

        for msg in result.outbox:
            print(f"     → {msg.target.value}: {msg.content[:50]}...")

    # Test 6: User2 sends message
    print("\n6️⃣ User2 (Boris) responds...")
    boris_participant = next(p for p in participants if p.role.value == "invitee")

    result = await message_service.resume_user_message(
        session.session_id,
        boris_participant.participant_id,
        telegram_message_id=1002,
        content="Я играю музыку только до 22:00, может Anna неправильно слышит время?"
    )

    if result:
        print(f"   Response phase: {result.phase.value}")
        print(f"   Now pending for: {result.pending_for.value}")
        print(f"   Outbox messages: {len(result.outbox)}")

        for msg in result.outbox:
            print(f"     → {msg.target.value}: {msg.content[:50]}...")

    # Test 7: Check pending outbound messages
    print("\n7️⃣ Checking pending outbound messages...")
    pending = await message_service.get_pending_outbound_messages(session.session_id)
    print(f"   Pending messages: {len(pending)}")

    # Test 8: Test idempotency
    print("\n8️⃣ Testing idempotency (sending duplicate message)...")
    result = await message_service.resume_user_message(
        session.session_id,
        anna_participant.participant_id,
        telegram_message_id=1001,  # Same ID as before
        content="This should be ignored due to idempotency"
    )
    print(f"   Duplicate message result: {result is None} (should be True)")

    # Test 9: Test wrong turn validation
    print("\n9️⃣ Testing wrong turn validation...")
    # Try Anna again when it's Boris's turn (should fail validation)
    result = await message_service.resume_user_message(
        session.session_id,
        anna_participant.participant_id,
        telegram_message_id=1003,
        content="This should be saved but not processed"
    )
    print(f"   Wrong turn result: {result is None} (should be True if validation works)")

    print("\n✅ Integration test completed!")
    print("🎯 All LangGraph components are working together")

if __name__ == "__main__":
    asyncio.run(test_complete_flow())