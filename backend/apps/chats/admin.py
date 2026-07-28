"""Django admin for chats — message bodies stay opaque.

Why: server-side encryption protects DB dumps and casual staff access.
Admin must never call MessageCrypto.decrypt; even superusers only see
ciphertext metadata, never plaintext.
"""

from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import Attachment, Chat, ChatMember, Message, MessageStatus


class ChatMemberInline(admin.TabularInline):
    model = ChatMember
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("joined_at",)


@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "title", "created_at", "updated_at")
    list_filter = ("type",)
    search_fields = ("title", "id")
    inlines = (ChatMemberInline,)
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ChatMember)
class ChatMemberAdmin(admin.ModelAdmin):
    list_display = ("id", "chat", "user", "role", "joined_at", "last_read_at")
    list_filter = ("role",)
    search_fields = ("user__username", "chat__title", "chat__id")
    autocomplete_fields = ("chat", "user")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Superuser-only, ciphertext-opaque message admin.

    Intentionally no decrypt path and no custom get_queryset that would
    hydrate plaintext for display.
    """

    list_display = (
        "id",
        "chat",
        "sender",
        "content_type",
        "ciphertext_size",
        "created_at",
        "edited_at",
        "is_deleted",
    )
    list_filter = ("content_type", "is_deleted", "created_at")
    search_fields = ("id", "chat__id")
    ordering = ("-created_at",)

    # Form shows opaque crypto fields only — never a "content" / plaintext widget.
    fields = (
        "id",
        "chat",
        "sender",
        "content_type",
        "ciphertext_repr",
        "nonce_repr",
        "created_at",
        "edited_at",
        "is_deleted",
    )
    readonly_fields = fields

    @admin.display(description="Ciphertext size")
    def ciphertext_size(self, obj: Message) -> str:
        data = bytes(obj.ciphertext or b"")
        if obj.is_deleted and not data:
            return "wiped"
        return f"{len(data)} bytes"

    @admin.display(description="Ciphertext")
    def ciphertext_repr(self, obj: Message) -> str:
        """Show opaque ciphertext only (truncated hex). Never decrypt."""
        data = bytes(obj.ciphertext or b"")
        if not data:
            return "—"
        preview = data[:48].hex()
        suffix = "…" if len(data) > 48 else ""
        return format_html(
            "<code>{}{}</code> <em>({} bytes, encrypted)</em>",
            preview,
            suffix,
            len(data),
        )

    @admin.display(description="Nonce")
    def nonce_repr(self, obj: Message) -> str:
        data = bytes(obj.nonce or b"")
        if not data:
            return "—"
        return format_html("<code>{}</code>", data.hex())

    def has_module_permission(self, request) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        # Read-only even for superusers — prevents accidental edits to ciphertext.
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)


@admin.register(MessageStatus)
class MessageStatusAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "user", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("message__id", "user__username")
    autocomplete_fields = ("message", "user")
    readonly_fields = ("updated_at",)

    def has_module_permission(self, request) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    """Opaque attachment metadata — never decrypt or serve file contents here."""

    list_display = (
        "id",
        "message",
        "original_filename",
        "mime_type",
        "size_bytes",
        "created_at",
    )
    search_fields = ("id", "message__id", "original_filename")
    readonly_fields = (
        "id",
        "message",
        "storage_path",
        "nonce",
        "mime_type",
        "size_bytes",
        "original_filename",
        "created_at",
    )

    def has_module_permission(self, request) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_view_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return bool(request.user.is_active and request.user.is_superuser)
