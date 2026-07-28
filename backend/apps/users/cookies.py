"""HttpOnly refresh-token cookie helpers.

Access tokens stay in the Authorization header (short-lived). Refresh tokens
are stored in a Secure + HttpOnly + SameSite cookie so XSS cannot exfiltrate
them as easily as localStorage.
"""

from __future__ import annotations

from django.conf import settings
from rest_framework.response import Response

REFRESH_COOKIE_NAME = "aio_refresh"


def set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        refresh_token,
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        httponly=True,
        secure=settings.REFRESH_COOKIE_SECURE,
        samesite=settings.REFRESH_COOKIE_SAMESITE,
        path="/api/auth/",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        REFRESH_COOKIE_NAME,
        path="/api/auth/",
        samesite=settings.REFRESH_COOKIE_SAMESITE,
    )


def get_refresh_from_request(request) -> str | None:
    return request.COOKIES.get(REFRESH_COOKIE_NAME) or None
