from __future__ import annotations

import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.test import RequestFactory

from apps.chats.admin import MessageAdmin
from apps.chats.models import Message
from apps.chats.services import ChatService, MessageService
from apps.crypto import message_crypto as crypto_module

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def rf() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def message_admin() -> MessageAdmin:
    return MessageAdmin(Message, AdminSite())


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="root", email="root@example.com", password="password123"
    )


@pytest.fixture
def staff_user(db):
    return User.objects.create_user(
        username="staffer", password="password123", is_staff=True
    )


@pytest.fixture
def sample_message(encryption_key):
    alice = User.objects.create_user(username="alice", password="password123")
    bob = User.objects.create_user(username="bob", password="password123")
    chat = ChatService.get_or_create_private_chat(creator=alice, other=bob)
    return MessageService.create_text_message(
        chat=chat, sender=alice, body="admin must not see this"
    )


class TestMessageAdminLockdown:
    def test_staff_cannot_view_messages(self, rf, message_admin, staff_user):
        request = rf.get("/admin/chats/message/")
        request.user = staff_user
        assert message_admin.has_module_permission(request) is False
        assert message_admin.has_view_permission(request) is False
        assert message_admin.has_change_permission(request) is False
        assert message_admin.has_add_permission(request) is False

    def test_superuser_can_view_but_not_edit(
        self, rf, message_admin, superuser, sample_message
    ):
        request = rf.get("/admin/chats/message/")
        request.user = superuser
        assert message_admin.has_module_permission(request) is True
        assert message_admin.has_view_permission(request, sample_message) is True
        assert message_admin.has_change_permission(request, sample_message) is False
        assert message_admin.has_add_permission(request) is False
        assert message_admin.has_delete_permission(request, sample_message) is True

    def test_admin_shows_ciphertext_not_plaintext(
        self, message_admin, sample_message, monkeypatch
    ):
        calls: list = []

        def boom(*args, **kwargs):
            calls.append(True)
            raise AssertionError("decrypt must not be called from admin")

        monkeypatch.setattr(crypto_module.MessageCrypto, "decrypt", boom)
        monkeypatch.setattr(crypto_module.MessageCrypto, "decrypt_text", boom)

        size = message_admin.ciphertext_size(sample_message)
        cipher = message_admin.ciphertext_repr(sample_message)
        nonce = message_admin.nonce_repr(sample_message)

        assert "bytes" in size
        assert "admin must not see this" not in str(cipher)
        assert "encrypted" in str(cipher)
        assert calls == []
        assert isinstance(nonce, str) or hasattr(nonce, "__html__")

    def test_list_display_has_no_plaintext_field(self, message_admin):
        assert "content" not in message_admin.list_display
        assert "ciphertext" not in message_admin.list_display
        assert "ciphertext_size" in message_admin.list_display
