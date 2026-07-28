"""Channel-layer helpers for chat realtime events.

Why separate from the consumer: REST create/delete must push the same events
as WebSocket sends, without importing consumer code into views.
"""

from __future__ import annotations

import json

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from rest_framework.renderers import JSONRenderer


def chat_group_name(chat_id) -> str:
    return f"chat_{chat_id}"


def to_json_safe(payload: dict) -> dict:
    """Normalize DRF/.data structures (UUIDs, decimals) for channel-layer JSON."""
    return json.loads(JSONRenderer().render(payload))


def broadcast_to_chat(*, chat_id, event_type: str, payload: dict) -> None:
    """Fan-out a JSON event to every socket joined to this chat group."""
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        chat_group_name(chat_id),
        {
            "type": "chat.event",  # -> ChatConsumer.chat_event
            "event_type": event_type,
            "payload": to_json_safe(payload),
        },
    )
