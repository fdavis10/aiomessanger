from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.users.serializers import UserPublicSerializer

from .models import Attachment, Chat, ChatMember, Message
from .services import ChatService, MessageService

User = get_user_model()


class ChatMemberSerializer(serializers.ModelSerializer):
    user = UserPublicSerializer(read_only=True)

    class Meta:
        model = ChatMember
        fields = ("id", "user", "role", "joined_at", "last_read_at")
        read_only_fields = fields


class ChatSerializer(serializers.ModelSerializer):
    members = ChatMemberSerializer(source="memberships", many=True, read_only=True)

    class Meta:
        model = Chat
        fields = (
            "id",
            "type",
            "title",
            "avatar",
            "created_at",
            "updated_at",
            "members",
        )
        read_only_fields = ("id", "created_at", "updated_at", "members")


class ChatCreateSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=Chat.ChatType.choices)
    title = serializers.CharField(required=False, allow_blank=True, max_length=255)
    user_id = serializers.IntegerField(required=False)
    member_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )

    def validate(self, attrs: dict) -> dict:
        chat_type = attrs["type"]
        if chat_type == Chat.ChatType.PRIVATE:
            if not attrs.get("user_id"):
                raise serializers.ValidationError(
                    {"user_id": "Required for private chats."}
                )
        elif chat_type == Chat.ChatType.GROUP:
            title = (attrs.get("title") or "").strip()
            if not title:
                raise serializers.ValidationError(
                    {"title": "Required for group chats."}
                )
            attrs["title"] = title
        return attrs

    def create(self, validated_data: dict) -> Chat:
        creator = self.context["request"].user
        if validated_data["type"] == Chat.ChatType.PRIVATE:
            other = User.objects.filter(
                pk=validated_data["user_id"], is_active=True
            ).first()
            if other is None:
                raise serializers.ValidationError({"user_id": "User not found."})
            try:
                return ChatService.get_or_create_private_chat(
                    creator=creator, other=other
                )
            except ValueError as exc:
                raise serializers.ValidationError({"user_id": str(exc)}) from exc

        return ChatService.create_group_chat(
            creator=creator,
            title=validated_data["title"],
            member_ids=validated_data.get("member_ids") or [],
        )


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = (
            "id",
            "mime_type",
            "size_bytes",
            "original_filename",
            "created_at",
        )
        read_only_fields = fields


class MessageSerializer(serializers.ModelSerializer):
    """Outbound message: decrypted body for authorized members only."""

    sender = UserPublicSerializer(read_only=True)
    content = serializers.SerializerMethodField()
    attachment = AttachmentSerializer(read_only=True)

    class Meta:
        model = Message
        fields = (
            "id",
            "chat",
            "sender",
            "content",
            "content_type",
            "attachment",
            "created_at",
            "edited_at",
            "is_deleted",
        )
        read_only_fields = fields

    def get_content(self, obj: Message) -> str | None:
        # Ciphertext/nonce must never appear in API responses at this stage.
        try:
            return MessageService.decrypt_content(obj)
        except Exception:
            # Fail closed: do not leak crypto errors or partial plaintext.
            return None


class MessageCreateSerializer(serializers.Serializer):
    content = serializers.CharField(max_length=10_000, allow_blank=False)
    content_type = serializers.ChoiceField(
        choices=[Message.ContentType.TEXT],
        default=Message.ContentType.TEXT,
        required=False,
    )

    def create(self, validated_data: dict) -> Message:
        chat: Chat = self.context["chat"]
        sender = self.context["request"].user
        return MessageService.create_text_message(
            chat=chat,
            sender=sender,
            body=validated_data["content"],
        )


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    caption = serializers.CharField(
        required=False, allow_blank=True, max_length=2000, default=""
    )
