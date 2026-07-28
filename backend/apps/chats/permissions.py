from __future__ import annotations

from django.contrib.auth import get_user_model

from .models import Chat, ChatMember

User = get_user_model()


def user_is_chat_member(*, chat: Chat, user: User) -> bool:
    """Membership check used by API/WS permission layers."""
    if not user.is_authenticated:
        return False
    return ChatMember.objects.filter(chat=chat, user=user).exists()


def get_user_chat_ids(user: User) -> list:
    """Chat IDs the user may join on the channel layer."""
    return list(
        ChatMember.objects.filter(user=user).values_list("chat_id", flat=True)
    )
