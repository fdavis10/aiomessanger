"""Key providers for the message encryption master key.

The master key must never live in the database. Today we load it from the
environment; later a Vault/KMS provider can replace EnvKeyProvider without
changing MessageCrypto call sites.
"""

from __future__ import annotations

import base64
from abc import ABC, abstractmethod
from typing import Final

from django.conf import settings

from .exceptions import EncryptionKeyError

AES_256_KEY_SIZE: Final[int] = 32


class KeyProvider(ABC):
    """Source of the AES-256 master key used for encryption at rest."""

    @abstractmethod
    def get_master_key(self) -> bytes:
        """Return a raw 32-byte AES-256 key."""


class StaticKeyProvider(KeyProvider):
    """In-memory key — for tests and future envelope-encryption data keys."""

    def __init__(self, key: bytes) -> None:
        if len(key) != AES_256_KEY_SIZE:
            raise EncryptionKeyError(
                f"AES-256 key must be {AES_256_KEY_SIZE} bytes, got {len(key)}"
            )
        self._key = key

    def get_master_key(self) -> bytes:
        return self._key


class EnvKeyProvider(KeyProvider):
    """Load MESSAGE_ENCRYPTION_KEY from settings (env / secret manager injection).

    Expected format: standard base64 encoding of exactly 32 random bytes.
    Generate with:
        python -c "import os,base64; print(base64.b64encode(os.urandom(32)).decode())"
    """

    def get_master_key(self) -> bytes:
        raw = getattr(settings, "MESSAGE_ENCRYPTION_KEY", "") or ""
        if not raw.strip():
            raise EncryptionKeyError(
                "MESSAGE_ENCRYPTION_KEY is not set. "
                "Provide a base64-encoded 32-byte key via the environment."
            )
        try:
            key = base64.b64decode(raw.strip(), validate=True)
        except Exception as exc:
            raise EncryptionKeyError(
                "MESSAGE_ENCRYPTION_KEY must be valid base64"
            ) from exc
        if len(key) != AES_256_KEY_SIZE:
            raise EncryptionKeyError(
                f"MESSAGE_ENCRYPTION_KEY must decode to {AES_256_KEY_SIZE} bytes, "
                f"got {len(key)}"
            )
        return key
