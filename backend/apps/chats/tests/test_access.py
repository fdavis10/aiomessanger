from __future__ import annotations

from pathlib import Path

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient

from apps.chats.models import Attachment
from apps.chats.services import ChatService, MessageService

User = get_user_model()

pytestmark = pytest.mark.django_db


@pytest.fixture
def api() -> APIClient:
    return APIClient()


@pytest.fixture
def users(db):
    a = User.objects.create_user(username="alice", password="password123")
    b = User.objects.create_user(username="bob", password="password123")
    c = User.objects.create_user(username="carol", password="password123")
    return a, b, c


def _auth(client: APIClient, user) -> APIClient:
    client.force_authenticate(user=user)
    return client


class TestAccessControl:
    def test_outsider_cannot_list_or_post_messages(
        self, api, users, encryption_key
    ):
        a, b, c = users
        chat = ChatService.get_or_create_private_chat(creator=a, other=b)
        MessageService.create_text_message(chat=chat, sender=a, body="secret")

        _auth(api, c)
        assert api.get(f"/api/chats/{chat.id}/messages/").status_code == 404
        assert (
            api.post(
                f"/api/chats/{chat.id}/messages/",
                {"content": "intrusion"},
                format="json",
            ).status_code
            == 404
        )
        assert api.get(f"/api/chats/{chat.id}/").status_code == 404
        assert api.get(f"/api/chats/{chat.id}/members/").status_code == 404

    def test_member_of_chat_a_cannot_read_chat_b(
        self, api, users, encryption_key
    ):
        a, b, c = users
        chat_ab = ChatService.get_or_create_private_chat(creator=a, other=b)
        chat_ac = ChatService.get_or_create_private_chat(creator=a, other=c)
        MessageService.create_text_message(
            chat=chat_ab, sender=a, body="only for bob"
        )
        MessageService.create_text_message(
            chat=chat_ac, sender=a, body="only for carol"
        )

        _auth(api, b)
        ab = api.get(f"/api/chats/{chat_ab.id}/messages/")
        assert ab.status_code == 200
        assert ab.data["results"][0]["content"] == "only for bob"
        assert api.get(f"/api/chats/{chat_ac.id}/messages/").status_code == 404

    def test_unauthenticated_api_denied(self, api, users, encryption_key):
        a, b, _ = users
        chat = ChatService.get_or_create_private_chat(creator=a, other=b)
        assert api.get("/api/chats/").status_code == 401
        assert api.get(f"/api/chats/{chat.id}/messages/").status_code == 401


class TestAttachments:
    def test_upload_encrypts_on_disk_and_member_can_download(
        self, api, users, encryption_key, settings, tmp_path
    ):
        settings.MEDIA_ROOT = tmp_path
        a, b, c = users
        chat = ChatService.get_or_create_private_chat(creator=a, other=b)

        _auth(api, a)
        upload = SimpleUploadedFile(
            "note.txt", b"hello attachment", content_type="text/plain"
        )
        resp = api.post(
            f"/api/chats/{chat.id}/attachments/",
            {"file": upload, "caption": "see file"},
            format="multipart",
        )
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["content"] == "see file"
        assert resp.data["attachment"]["original_filename"] == "note.txt"
        attachment_id = resp.data["attachment"]["id"]

        att = Attachment.objects.get(pk=attachment_id)
        disk = Path(settings.MEDIA_ROOT) / att.storage_path
        assert disk.is_file()
        assert b"hello attachment" not in disk.read_bytes()

        _auth(api, b)
        download = api.get(f"/api/attachments/{attachment_id}/download/")
        assert download.status_code == 200
        assert b"".join(download.streaming_content) == b"hello attachment"

        _auth(api, c)
        assert (
            api.get(f"/api/attachments/{attachment_id}/download/").status_code
            == 404
        )

    def test_outsider_cannot_upload(self, api, users, encryption_key, settings, tmp_path):
        settings.MEDIA_ROOT = tmp_path
        a, b, c = users
        chat = ChatService.get_or_create_private_chat(creator=a, other=b)
        _auth(api, c)
        upload = SimpleUploadedFile("x.txt", b"nope", content_type="text/plain")
        assert (
            api.post(
                f"/api/chats/{chat.id}/attachments/",
                {"file": upload},
                format="multipart",
            ).status_code
            == 404
        )


class TestAuthCookies:
    def test_register_sets_refresh_cookie(self, api):
        resp = api.post(
            "/api/auth/register/",
            {"username": "cookied", "password": "password123"},
            format="json",
        )
        assert resp.status_code == 201
        assert "aio_refresh" in resp.cookies
        cookie = resp.cookies["aio_refresh"]
        assert cookie["httponly"] is True or cookie["httponly"] == True
