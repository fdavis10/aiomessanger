from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

from apps.chats.models import Chat, ChatMember, Message
from apps.chats.services import ChatService, MessageService

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def user_a(db):
    return User.objects.create_user(username="alice", password="password123")


@pytest.fixture
def user_b(db):
    return User.objects.create_user(username="bob", password="password123")


@pytest.fixture
def user_c(db):
    return User.objects.create_user(username="carol", password="password123")


def _auth(client: APIClient, user) -> APIClient:
    client.force_authenticate(user=user)
    return client


class TestAuth:
    def test_register_returns_tokens(self, api):
        resp = api.post(
            "/api/auth/register/",
            {"username": "newbie", "password": "password123", "email": "n@e.com"},
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["username"] == "newbie"

    def test_me_requires_auth(self, api):
        assert api.get("/api/users/me/").status_code == status.HTTP_401_UNAUTHORIZED


class TestChatsAndMessages:
    def test_private_chat_and_encrypted_message_roundtrip(
        self, api, user_a, user_b, encryption_key
    ):
        _auth(api, user_a)
        create = api.post(
            "/api/chats/",
            {"type": "private", "user_id": user_b.id},
            format="json",
        )
        assert create.status_code == status.HTTP_201_CREATED
        chat_id = create.data["id"]

        send = api.post(
            f"/api/chats/{chat_id}/messages/",
            {"content": "hello bob"},
            format="json",
        )
        assert send.status_code == status.HTTP_201_CREATED
        assert send.data["content"] == "hello bob"
        assert "ciphertext" not in send.data
        assert "nonce" not in send.data

        message = Message.objects.get(pk=send.data["id"])
        assert bytes(message.ciphertext) != b"hello bob"
        assert MessageService.decrypt_content(message) == "hello bob"

        listing = api.get(f"/api/chats/{chat_id}/messages/")
        assert listing.status_code == status.HTTP_200_OK
        assert listing.data["results"][0]["content"] == "hello bob"

    def test_outsider_cannot_read_messages(
        self, api, user_a, user_b, user_c, encryption_key
    ):
        chat = ChatService.get_or_create_private_chat(creator=user_a, other=user_b)
        MessageService.create_text_message(
            chat=chat, sender=user_a, body="top secret"
        )

        _auth(api, user_c)
        resp = api.get(f"/api/chats/{chat.id}/messages/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

        detail = api.get(f"/api/chats/{chat.id}/")
        assert detail.status_code == status.HTTP_404_NOT_FOUND

    def test_member_list_isolated(self, api, user_a, user_b, user_c):
        chat_ab = ChatService.get_or_create_private_chat(creator=user_a, other=user_b)
        ChatService.get_or_create_private_chat(creator=user_a, other=user_c)

        _auth(api, user_b)
        resp = api.get("/api/chats/")
        assert resp.status_code == status.HTTP_200_OK
        ids = {c["id"] for c in resp.data["results"]}
        assert str(chat_ab.id) in ids
        assert len(ids) == 1

    def test_plaintext_not_stored(self, user_a, user_b, encryption_key):
        chat = ChatService.get_or_create_private_chat(creator=user_a, other=user_b)
        msg = MessageService.create_text_message(
            chat=chat, sender=user_a, body="plain-in-db?"
        )
        raw = Message.objects.values("ciphertext", "nonce").get(pk=msg.pk)
        assert b"plain-in-db?" not in bytes(raw["ciphertext"])

    def test_group_chat_create(self, api, user_a, user_b, user_c):
        _auth(api, user_a)
        resp = api.post(
            "/api/chats/",
            {
                "type": "group",
                "title": "Squad",
                "member_ids": [user_b.id, user_c.id],
            },
            format="json",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["type"] == "group"
        assert resp.data["title"] == "Squad"
        assert len(resp.data["members"]) == 3
