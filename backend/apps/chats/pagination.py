from django.utils import timezone
from rest_framework.pagination import CursorPagination


class MessageCursorPagination(CursorPagination):
    """Newest-first cursor pagination for long chat histories."""

    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-created_at", "-id")


class ChatCursorPagination(CursorPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = ("-updated_at", "-id")


def touch_chat(chat) -> None:
    chat.updated_at = timezone.now()
    chat.save(update_fields=["updated_at"])


def chat_aad(chat_id) -> bytes:
    """Bind ciphertext to a chat so payloads cannot be moved across chats."""
    return f"chat:{chat_id}".encode("utf-8")
