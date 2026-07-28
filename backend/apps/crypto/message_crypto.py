"""AES-256-GCM encryption for message/media payloads at rest.

This is server-side encryption (not E2EE): the server holds the key and can
decrypt. The API surface is intentionally narrow (ciphertext + nonce) so a
future client-side crypto layer can replace MessageCrypto without rewriting
storage models.
"""

from __future__ import annotations

import os
from typing import Final

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .exceptions import DecryptionError, EncryptionKeyError
from .key_providers import EnvKeyProvider, KeyProvider

NONCE_SIZE: Final[int] = 12  # 96-bit nonce recommended for AES-GCM


class MessageCrypto:
    """Encrypt/decrypt payloads with AES-256-GCM and a per-message nonce."""

    def __init__(self, key_provider: KeyProvider | None = None) -> None:
        self._key_provider = key_provider or EnvKeyProvider()

    def _aesgcm(self) -> AESGCM:
        try:
            key = self._key_provider.get_master_key()
        except EncryptionKeyError:
            raise
        except Exception as exc:
            raise EncryptionKeyError("Failed to load encryption key") from exc
        return AESGCM(key)

    def encrypt(
        self,
        plaintext: str | bytes,
        *,
        associated_data: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        """Encrypt plaintext.

        Returns (ciphertext, nonce). Never reuse a nonce with the same key.
        Optional associated_data is authenticated but not encrypted (e.g. chat_id)
        so ciphertext cannot be moved across contexts undetected.
        """
        if isinstance(plaintext, str):
            plaintext_bytes = plaintext.encode("utf-8")
        else:
            plaintext_bytes = plaintext

        nonce = os.urandom(NONCE_SIZE)
        ciphertext = self._aesgcm().encrypt(nonce, plaintext_bytes, associated_data)
        return ciphertext, nonce

    def decrypt(
        self,
        ciphertext: bytes,
        nonce: bytes,
        *,
        associated_data: bytes | None = None,
    ) -> bytes:
        """Decrypt and authenticate ciphertext. Raises DecryptionError on tamper."""
        if len(nonce) != NONCE_SIZE:
            raise DecryptionError(
                f"Nonce must be {NONCE_SIZE} bytes, got {len(nonce)}"
            )
        try:
            return self._aesgcm().decrypt(nonce, ciphertext, associated_data)
        except InvalidTag as exc:
            # GCM integrity failure — treat as tamper / wrong key / wrong AAD
            raise DecryptionError("Ciphertext authentication failed") from exc
        except DecryptionError:
            raise
        except EncryptionKeyError:
            raise
        except Exception as exc:
            raise DecryptionError("Decryption failed") from exc

    def encrypt_text(
        self,
        plaintext: str,
        *,
        associated_data: bytes | None = None,
    ) -> tuple[bytes, bytes]:
        return self.encrypt(plaintext, associated_data=associated_data)

    def decrypt_text(
        self,
        ciphertext: bytes,
        nonce: bytes,
        *,
        associated_data: bytes | None = None,
    ) -> str:
        return self.decrypt(
            ciphertext, nonce, associated_data=associated_data
        ).decode("utf-8")


def get_message_crypto() -> MessageCrypto:
    """Default factory wired to EnvKeyProvider (swap later for KMS/Vault)."""
    return MessageCrypto(key_provider=EnvKeyProvider())
