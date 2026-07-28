"""Temporary DEV-ONLY seed: create demo users if missing.

Runs when Daphne/ASGI starts (DEBUG only). Remove when real onboarding exists.
"""

from __future__ import annotations

import logging
import os
import sys

from django.apps import apps
from django.conf import settings
from django.db import OperationalError, ProgrammingError

logger = logging.getLogger(__name__)

# Plain passwords for local hybrid/dev only — never for production.
DEV_USERS: list[dict[str, str]] = [
    {
        "username": "alice",
        "password": "Devpass123!",
        "email": "alice@example.com",
        "first_name": "Alice",
        "phone": "+7 900 111-22-33",
        "bio": "Encrypted chats, clear mind.",
    },
    {
        "username": "bob",
        "password": "Devpass123!",
        "email": "bob@example.com",
        "first_name": "Bob",
        "phone": "+7 900 444-55-66",
        "bio": "Always online for a quick ping.",
    },
    {
        "username": "charlie",
        "password": "Devpass123!",
        "email": "charlie@example.com",
        "first_name": "Charlie",
        "phone": "+7 900 777-88-99",
        "bio": "",
    },
]


def _should_seed() -> bool:
    if not settings.DEBUG:
        return False
    module = os.environ.get("DJANGO_SETTINGS_MODULE", "")
    if module.endswith("settings_test"):
        return False
    if any(arg in {"test", "makemigrations", "migrate"} for arg in sys.argv):
        return False
    return True


def ensure_dev_users() -> list[str]:
    """Create missing demo users (and fill empty profile fields). Returns created usernames."""
    if not _should_seed():
        return []

    if not apps.ready:
        return []

    User = apps.get_model("users", "User")
    created: list[str] = []

    try:
        for spec in DEV_USERS:
            username = spec["username"]
            user = User.objects.filter(username=username).first()
            if user is None:
                user = User.objects.create_user(
                    username=username,
                    email=spec.get("email", ""),
                    password=spec["password"],
                    first_name=spec.get("first_name", ""),
                    phone=spec.get("phone", ""),
                    bio=spec.get("bio", ""),
                )
                created.append(username)
                continue

            dirty = False
            for field in ("phone", "bio", "first_name"):
                if not getattr(user, field, "") and spec.get(field):
                    setattr(user, field, spec[field])
                    dirty = True
            if dirty:
                user.save(update_fields=["phone", "bio", "first_name"])
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Dev user seed skipped (DB not ready): %s", exc)
        return []

    if created:
        logger.warning(
            "DEV seed: created users %s (password for all: Devpass123!)",
            ", ".join(created),
        )
    else:
        logger.info("DEV seed: demo users already present")

    return created
