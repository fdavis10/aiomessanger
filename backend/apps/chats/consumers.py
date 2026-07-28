"""Realtime chat WebSocket consumer.

Flow: authenticate via JWT → verify chat membership → join chat group.
Inbound messages are encrypted at rest before broadcast; outbound payloads
carry plaintext over the TLS/WSS channel (not E2EE yet).
"""

from __future__ import annotations

import logging
from typing import Any

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.utils import timezone

from .models import ChatMember, Message, MessageStatus
from .realtime import chat_group_name, to_json_safe
from .serializers import MessageSerializer
from .services import MessageService

logger = logging.getLogger(__name__)

# Close codes reserved for app-level authz (4000–4999).
CLOSE_UNAUTHORIZED = 4001
CLOSE_FORBIDDEN = 4003


class ChatConsumer(AsyncJsonWebsocketConsumer):
    chat_id: str
    group_name: str

    async def connect(self) -> None:
        user = self.scope.get("user")
        if user is None or not user.is_authenticated:
            await self.close(code=CLOSE_UNAUTHORIZED)
            return

        self.chat_id = str(self.scope["url_route"]["kwargs"]["chat_id"])
        if not await self._is_member(self.chat_id, user.id):
            await self.close(code=CLOSE_FORBIDDEN)
            return

        self.group_name = chat_group_name(self.chat_id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self._touch_last_seen(user.id)
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.event",
                "event_type": "presence.online",
                "payload": {"user_id": user.id, "chat_id": self.chat_id},
            },
        )

    async def disconnect(self, code: int) -> None:
        user = self.scope.get("user")
        if hasattr(self, "group_name") and user is not None and user.is_authenticated:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self._touch_last_seen(user.id)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.event",
                    "event_type": "presence.offline",
                    "payload": {"user_id": user.id, "chat_id": self.chat_id},
                },
            )

    async def receive_json(self, content: dict[str, Any], **kwargs) -> None:
        user = self.scope["user"]
        event_type = content.get("type")
        payload = content.get("payload") or {}

        if event_type == "message.send":
            await self._handle_message_send(user, payload)
        elif event_type == "message.delete":
            await self._handle_message_delete(user, payload)
        elif event_type == "typing":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "chat.event",
                    "event_type": "typing",
                    "payload": {
                        "chat_id": self.chat_id,
                        "user_id": user.id,
                        "is_typing": bool(payload.get("is_typing", True)),
                    },
                },
            )
        elif event_type == "read.receipt":
            await self._handle_read_receipt(user, payload)
        else:
            await self.send_json(
                {"type": "error", "payload": {"detail": "Unknown event type"}}
            )

    async def chat_event(self, event: dict[str, Any]) -> None:
        """Handler for channel-layer group_send(type='chat.event')."""
        await self.send_json(
            {"type": event["event_type"], "payload": event["payload"]}
        )

    async def _handle_message_send(self, user, payload: dict) -> None:
        content = (payload.get("content") or "").strip()
        if not content:
            await self.send_json(
                {"type": "error", "payload": {"detail": "content is required"}}
            )
            return
        if len(content) > 10_000:
            await self.send_json(
                {"type": "error", "payload": {"detail": "content too long"}}
            )
            return

        message_data = await self._create_message(user.id, content)
        # Broadcast is done inside MessageService.create_text_message.
        await self.send_json(
            {"type": "message.ack", "payload": to_json_safe(message_data)}
        )

    async def _handle_message_delete(self, user, payload: dict) -> None:
        message_id = payload.get("message_id")
        if not message_id:
            await self.send_json(
                {"type": "error", "payload": {"detail": "message_id is required"}}
            )
            return
        try:
            result = await self._soft_delete_message(user.id, str(message_id))
        except PermissionError as exc:
            await self.send_json(
                {"type": "error", "payload": {"detail": str(exc)}}
            )
            return
        except Message.DoesNotExist:
            await self.send_json(
                {"type": "error", "payload": {"detail": "Message not found"}}
            )
            return

        await self.send_json({"type": "message.ack", "payload": result})

    async def _handle_read_receipt(self, user, payload: dict) -> None:
        message_id = payload.get("message_id")
        if not message_id:
            return
        ok = await self._mark_read(user.id, str(message_id))
        if not ok:
            return
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "chat.event",
                "event_type": "read.receipt",
                "payload": {
                    "chat_id": self.chat_id,
                    "message_id": str(message_id),
                    "user_id": user.id,
                },
            },
        )

    @database_sync_to_async
    def _is_member(self, chat_id: str, user_id: int) -> bool:
        return ChatMember.objects.filter(chat_id=chat_id, user_id=user_id).exists()

    @database_sync_to_async
    def _touch_last_seen(self, user_id: int) -> None:
        from django.contrib.auth import get_user_model

        get_user_model().objects.filter(pk=user_id).update(last_seen_at=timezone.now())

    @database_sync_to_async
    def _create_message(self, user_id: int, content: str) -> dict:
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(pk=user_id)
        from .models import Chat

        chat = Chat.objects.get(pk=self.chat_id)
        message = MessageService.create_text_message(
            chat=chat, sender=user, body=content
        )
        message = Message.objects.select_related("sender").get(pk=message.pk)
        return MessageSerializer(message).data

    @database_sync_to_async
    def _soft_delete_message(self, user_id: int, message_id: str) -> dict:
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.get(pk=user_id)
        message = Message.objects.get(pk=message_id, chat_id=self.chat_id)
        MessageService.soft_delete(message=message, actor=user)
        return {
            "id": str(message_id),
            "chat": self.chat_id,
            "is_deleted": True,
        }

    @database_sync_to_async
    def _mark_read(self, user_id: int, message_id: str) -> bool:
        try:
            message = Message.objects.get(pk=message_id, chat_id=self.chat_id)
        except Message.DoesNotExist:
            return False
        MessageStatus.objects.update_or_create(
            message=message,
            user_id=user_id,
            defaults={"status": MessageStatus.Status.READ},
        )
        ChatMember.objects.filter(chat_id=self.chat_id, user_id=user_id).update(
            last_read_at=timezone.now()
        )
        return True
