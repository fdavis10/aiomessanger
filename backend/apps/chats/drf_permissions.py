from __future__ import annotations

from rest_framework.permissions import BasePermission, SAFE_METHODS

from .models import Chat, ChatMember, Message
from .permissions import user_is_chat_member


class IsChatMember(BasePermission):
    """Object-level: only chat members may read/write the chat or its messages."""

    def has_object_permission(self, request, view, obj) -> bool:
        chat = _resolve_chat(obj)
        if chat is None:
            return False
        return user_is_chat_member(chat=chat, user=request.user)


class IsChatMemberOrReadOnlyOwner(BasePermission):
    """Members can read; mutating group metadata requires owner/admin."""

    def has_object_permission(self, request, view, obj) -> bool:
        chat = _resolve_chat(obj)
        if chat is None:
            return False
        if not user_is_chat_member(chat=chat, user=request.user):
            return False
        if request.method in SAFE_METHODS:
            return True
        return ChatMember.objects.filter(
            chat=chat,
            user=request.user,
            role__in=(ChatMember.Role.OWNER, ChatMember.Role.ADMIN),
        ).exists()


def _resolve_chat(obj) -> Chat | None:
    if isinstance(obj, Chat):
        return obj
    if isinstance(obj, Message):
        return obj.chat
    if isinstance(obj, ChatMember):
        return obj.chat
    return None
