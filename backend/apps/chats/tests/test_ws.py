from __future__ import annotations

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

from apps.chats.models import Message
from apps.chats.services import ChatService
from config.asgi import application

User = get_user_model()

pytestmark = pytest.mark.django_db(transaction=True)


def _token_for(user) -> str:
    return str(AccessToken.for_user(user))


@database_sync_to_async
def _create_chat(a, b):
    return ChatService.get_or_create_private_chat(creator=a, other=b)


@database_sync_to_async
def _get_message(message_id: str) -> Message:
    return Message.objects.get(pk=message_id)


async def _connect(chat_id, user) -> WebsocketCommunicator:
    communicator = WebsocketCommunicator(
        application,
        f"/ws/chats/{chat_id}/?token={_token_for(user)}",
    )
    connected, _ = await communicator.connect()
    assert connected is True
    event = await communicator.receive_json_from()
    assert event["type"] == "presence.online"
    return communicator


@pytest.fixture
def users(db):
    a = User.objects.create_user(username="alice", password="password123")
    b = User.objects.create_user(username="bob", password="password123")
    c = User.objects.create_user(username="carol", password="password123")
    return a, b, c


class TestChatWebSocket:
    @pytest.mark.asyncio
    async def test_rejects_unauthenticated(self, users, encryption_key):
        a, b, _ = users
        chat = await _create_chat(a, b)
        communicator = WebsocketCommunicator(
            application, f"/ws/chats/{chat.id}/"
        )
        connected, code = await communicator.connect()
        assert connected is False
        assert code == 4001
        await communicator.wait()

    @pytest.mark.asyncio
    async def test_rejects_non_member(self, users, encryption_key):
        a, b, c = users
        chat = await _create_chat(a, b)
        communicator = WebsocketCommunicator(
            application,
            f"/ws/chats/{chat.id}/?token={_token_for(c)}",
        )
        connected, code = await communicator.connect()
        assert connected is False
        assert code == 4003
        await communicator.wait()

    @pytest.mark.asyncio
    async def test_member_send_receive_and_encrypt(
        self, users, encryption_key
    ):
        a, b, _ = users
        chat = await _create_chat(a, b)

        alice_ws = await _connect(chat.id, a)
        bob_ws = await _connect(chat.id, b)

        online = await alice_ws.receive_json_from()
        assert online["type"] == "presence.online"
        assert online["payload"]["user_id"] == b.id

        await alice_ws.send_json_to(
            {"type": "message.send", "payload": {"content": "ws hello"}}
        )

        # Expect message.ack and message.new on alice; message.new on bob.
        # Order between ack and broadcast is not guaranteed.
        alice_events = [
            await alice_ws.receive_json_from(),
            await alice_ws.receive_json_from(),
        ]
        bob_event = await bob_ws.receive_json_from()

        alice_types = {e["type"] for e in alice_events}
        assert alice_types == {"message.ack", "message.new"}
        assert bob_event["type"] == "message.new"
        assert bob_event["payload"]["content"] == "ws hello"
        assert "ciphertext" not in bob_event["payload"]

        new_payload = next(
            e["payload"] for e in alice_events if e["type"] == "message.new"
        )
        message = await _get_message(new_payload["id"])
        assert b"ws hello" not in bytes(message.ciphertext)

        await alice_ws.disconnect()
        await bob_ws.disconnect()

    @pytest.mark.asyncio
    async def test_typing_relay(self, users, encryption_key):
        a, b, _ = users
        chat = await _create_chat(a, b)
        alice_ws = await _connect(chat.id, a)
        bob_ws = await _connect(chat.id, b)
        await alice_ws.receive_json_from()  # bob online

        await alice_ws.send_json_to(
            {"type": "typing", "payload": {"is_typing": True}}
        )
        for ws in (alice_ws, bob_ws):
            event = await ws.receive_json_from()
            assert event["type"] == "typing"
            assert event["payload"]["user_id"] == a.id
            assert event["payload"]["is_typing"] is True

        await alice_ws.disconnect()
        await bob_ws.disconnect()
