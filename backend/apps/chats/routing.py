from __future__ import annotations

from django.urls import path

from .consumers import ChatConsumer, InboxConsumer

websocket_urlpatterns = [
    path("ws/inbox/", InboxConsumer.as_asgi()),
    path("ws/chats/<uuid:chat_id>/", ChatConsumer.as_asgi()),
]
