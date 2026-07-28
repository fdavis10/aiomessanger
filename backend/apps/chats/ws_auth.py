"""JWT authentication for WebSocket handshakes.

Browsers cannot set Authorization on WS easily, so the access token is accepted
from ?token=… query string (primary) or an Authorization: Bearer header.
"""

from __future__ import annotations

from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()


def _extract_token(scope: dict) -> str | None:
    query = parse_qs(scope.get("query_string", b"").decode())
    raw = query.get("token", [None])[0]
    if raw:
        return raw

    headers = dict(scope.get("headers") or [])
    auth = headers.get(b"authorization", b"").decode()
    if auth.lower().startswith("bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


@database_sync_to_async
def _user_from_token(raw_token: str):
    try:
        access = AccessToken(raw_token)
        user_id = access.get("user_id")
        if user_id is None:
            return AnonymousUser()
        user = User.objects.filter(pk=user_id, is_active=True).first()
        return user or AnonymousUser()
    except (InvalidToken, TokenError, Exception):
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            token = _extract_token(scope)
            if token:
                scope["user"] = await _user_from_token(token)
            else:
                scope["user"] = AnonymousUser()
        return await super().__call__(scope, receive, send)


def JwtAuthMiddlewareStack(inner):
    return JwtAuthMiddleware(inner)
