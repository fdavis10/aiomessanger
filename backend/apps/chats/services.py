from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404

from apps.crypto.services import get_message_crypto

from .models import Attachment, Chat, ChatMember, Message
from .pagination import chat_aad, touch_chat

User = get_user_model()


class ChatService:
    @staticmethod
    @transaction.atomic
    def get_or_create_private_chat(*, creator: User, other: User) -> Chat:
        if creator.pk == other.pk:
            raise ValueError("Cannot create a private chat with yourself")

        existing = (
            Chat.objects.filter(type=Chat.ChatType.PRIVATE, memberships__user=creator)
            .filter(memberships__user=other)
            .distinct()
            .first()
        )
        if existing is not None:
            return existing

        chat = Chat.objects.create(type=Chat.ChatType.PRIVATE)
        ChatMember.objects.create(
            chat=chat, user=creator, role=ChatMember.Role.OWNER
        )
        ChatMember.objects.create(
            chat=chat, user=other, role=ChatMember.Role.MEMBER
        )
        return chat

    @staticmethod
    @transaction.atomic
    def create_group_chat(
        *,
        creator: User,
        title: str,
        member_ids: list[int],
    ) -> Chat:
        chat = Chat.objects.create(type=Chat.ChatType.GROUP, title=title.strip())
        ChatMember.objects.create(
            chat=chat, user=creator, role=ChatMember.Role.OWNER
        )
        unique_ids = {mid for mid in member_ids if mid != creator.pk}
        users = list(User.objects.filter(pk__in=unique_ids, is_active=True))
        ChatMember.objects.bulk_create(
            [
                ChatMember(chat=chat, user=user, role=ChatMember.Role.MEMBER)
                for user in users
            ]
        )
        return chat


class MessageService:
    @staticmethod
    @transaction.atomic
    def create_text_message(
        *,
        chat: Chat,
        sender: User,
        body: str,
    ) -> Message:
        crypto = get_message_crypto()
        ciphertext, nonce = crypto.encrypt_text(
            body, associated_data=chat_aad(chat.pk)
        )
        message = Message.objects.create(
            chat=chat,
            sender=sender,
            ciphertext=ciphertext,
            nonce=bytes(nonce),
            content_type=Message.ContentType.TEXT,
        )
        touch_chat(chat)
        message = Message.objects.select_related("sender").get(pk=message.pk)
        # Lazy import avoids circular dependency with serializers.
        from .realtime import broadcast_to_chat
        from .serializers import MessageSerializer

        broadcast_to_chat(
            chat_id=chat.pk,
            event_type="message.new",
            payload=MessageSerializer(message).data,
        )
        return message

    @staticmethod
    def decrypt_content(message: Message) -> str | None:
        if message.is_deleted:
            return None
        crypto = get_message_crypto()
        return crypto.decrypt_text(
            bytes(message.ciphertext),
            bytes(message.nonce),
            associated_data=chat_aad(message.chat_id),
        )

    @staticmethod
    @transaction.atomic
    def soft_delete(*, message: Message, actor: User) -> Message:
        if message.sender_id != actor.pk:
            raise PermissionError("Only the sender can delete this message")
        message.is_deleted = True
        # Wipe ciphertext so a DB dump after delete cannot recover content
        # even with the master key (best-effort; already-read clients may cache).
        message.ciphertext = b""
        message.nonce = b""
        message.save(update_fields=["is_deleted", "ciphertext", "nonce"])
        attachment = Attachment.objects.filter(message=message).first()
        if attachment is not None:
            from .attachments import AttachmentService

            AttachmentService.wipe_storage(attachment=attachment)
            attachment.nonce = b""
            attachment.save(update_fields=["nonce"])
        touch_chat(message.chat)
        from .realtime import broadcast_to_chat

        broadcast_to_chat(
            chat_id=message.chat_id,
            event_type="message.deleted",
            payload={
                "id": str(message.pk),
                "chat": str(message.chat_id),
                "is_deleted": True,
            },
        )
        return message


def get_chat_for_member(*, chat_id, user: User) -> Chat:
    """Return chat only if user is a member; otherwise 404 (hide existence)."""
    try:
        chat = Chat.objects.get(pk=chat_id)
    except Chat.DoesNotExist as exc:
        raise Http404 from exc
    if not ChatMember.objects.filter(chat=chat, user=user).exists():
        raise Http404
    return chat
