from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Chat(models.Model):
    """Private or group conversation.

    Message bodies are never stored here — only membership and metadata.
    """

    class ChatType(models.TextChoices):
        PRIVATE = "private", _("Private")
        GROUP = "group", _("Group")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type = models.CharField(
        max_length=16,
        choices=ChatType.choices,
        default=ChatType.PRIVATE,
        db_index=True,
    )
    title = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text=_("Display name for group chats; unused for private chats."),
    )
    avatar = models.ImageField(upload_to="chat_avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="ChatMember",
        related_name="chats",
    )

    class Meta:
        ordering = ("-updated_at",)
        verbose_name = _("chat")
        verbose_name_plural = _("chats")

    def __str__(self) -> str:
        if self.type == self.ChatType.GROUP and self.title:
            return self.title
        return f"{self.get_type_display()} {self.pk}"


class ChatMember(models.Model):
    """Membership + role for a user in a chat."""

    class Role(models.TextChoices):
        OWNER = "owner", _("Owner")
        ADMIN = "admin", _("Admin")
        MEMBER = "member", _("Member")

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_memberships",
    )
    role = models.CharField(
        max_length=16,
        choices=Role.choices,
        default=Role.MEMBER,
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    # Denormalized cursor for "last read" UX; detailed receipts live in MessageStatus.
    last_read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("chat", "user"),
                name="chats_chatmember_unique_chat_user",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "joined_at")),
        ]
        verbose_name = _("chat member")
        verbose_name_plural = _("chat members")

    def __str__(self) -> str:
        return f"{self.user_id} in {self.chat_id} ({self.role})"


class Message(models.Model):
    """Encrypted message payload.

    Only ciphertext + nonce are persisted — never plaintext. Encrypt/decrypt
    exclusively in the application layer (serializers/services/consumers).
    """

    class ContentType(models.TextChoices):
        TEXT = "text", _("Text")
        IMAGE = "image", _("Image")
        VIDEO = "video", _("Video")
        FILE = "file", _("File")
        SYSTEM = "system", _("System")

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="messages",
        help_text=_("Null for system messages."),
    )
    # Opaque AES-GCM ciphertext (includes auth tag). Never store plaintext here.
    ciphertext = models.BinaryField()
    # Per-message 12-byte nonce; must never be reused with the same key.
    nonce = models.BinaryField()
    content_type = models.CharField(
        max_length=16,
        choices=ContentType.choices,
        default=ContentType.TEXT,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    edited_at = models.DateTimeField(null=True, blank=True)
    is_deleted = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            # Cursor pagination over a chat timeline.
            models.Index(fields=("chat", "-created_at", "-id")),
        ]
        verbose_name = _("message")
        verbose_name_plural = _("messages")

    def __str__(self) -> str:
        # Do not include any decryptable content in string representations / logs.
        return f"Message {self.pk} in chat {self.chat_id}"


class MessageStatus(models.Model):
    """Per-user delivery / read receipt for a message."""

    class Status(models.TextChoices):
        DELIVERED = "delivered", _("Delivered")
        READ = "read", _("Read")

    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="statuses",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="message_statuses",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.DELIVERED,
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("message", "user"),
                name="chats_messagestatus_unique_message_user",
            ),
        ]
        indexes = [
            models.Index(fields=("user", "status", "updated_at")),
        ]
        verbose_name = _("message status")
        verbose_name_plural = _("message statuses")

    def __str__(self) -> str:
        return f"{self.status} by {self.user_id} on {self.message_id}"


class Attachment(models.Model):
    """Encrypted media blob stored on disk (opaque path, never original filename).

    File bytes are AES-GCM encrypted before write. Download decrypts only for
    chat members via the application layer — never serve raw storage files.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.OneToOneField(
        Message,
        on_delete=models.CASCADE,
        related_name="attachment",
    )
    # Relative path under MEDIA_ROOT; basename is random — not the user filename.
    storage_path = models.CharField(max_length=512)
    nonce = models.BinaryField()
    mime_type = models.CharField(max_length=128, blank=True, default="")
    size_bytes = models.PositiveIntegerField()
    # Display name for members; on-disk object is never named this.
    original_filename = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("attachment")
        verbose_name_plural = _("attachments")

    def __str__(self) -> str:
        return f"Attachment {self.pk} for message {self.message_id}"
