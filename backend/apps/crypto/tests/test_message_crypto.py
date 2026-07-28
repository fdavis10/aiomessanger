from __future__ import annotations

import base64
import os

import pytest
from django.test import override_settings

from apps.crypto.exceptions import DecryptionError, EncryptionKeyError
from apps.crypto.key_providers import EnvKeyProvider, StaticKeyProvider
from apps.crypto.message_crypto import NONCE_SIZE, MessageCrypto, get_message_crypto


@pytest.fixture
def master_key() -> bytes:
    return os.urandom(32)


@pytest.fixture
def crypto(master_key: bytes) -> MessageCrypto:
    return MessageCrypto(key_provider=StaticKeyProvider(master_key))


class TestStaticKeyProvider:
    def test_rejects_wrong_key_length(self) -> None:
        with pytest.raises(EncryptionKeyError):
            StaticKeyProvider(b"too-short")

    def test_returns_key(self, master_key: bytes) -> None:
        assert StaticKeyProvider(master_key).get_master_key() == master_key


class TestEnvKeyProvider:
    def test_missing_key_raises(self) -> None:
        with override_settings(MESSAGE_ENCRYPTION_KEY=""):
            with pytest.raises(EncryptionKeyError):
                EnvKeyProvider().get_master_key()

    def test_invalid_base64_raises(self) -> None:
        with override_settings(MESSAGE_ENCRYPTION_KEY="not-valid-base64!!!"):
            with pytest.raises(EncryptionKeyError):
                EnvKeyProvider().get_master_key()

    def test_wrong_decoded_length_raises(self) -> None:
        short = base64.b64encode(os.urandom(16)).decode()
        with override_settings(MESSAGE_ENCRYPTION_KEY=short):
            with pytest.raises(EncryptionKeyError):
                EnvKeyProvider().get_master_key()

    def test_loads_valid_key(self, master_key: bytes) -> None:
        encoded = base64.b64encode(master_key).decode()
        with override_settings(MESSAGE_ENCRYPTION_KEY=encoded):
            assert EnvKeyProvider().get_master_key() == master_key


class TestMessageCrypto:
    def test_encrypt_decrypt_roundtrip_text(self, crypto: MessageCrypto) -> None:
        plaintext = "привет, messenger — 🔐"
        ciphertext, nonce = crypto.encrypt_text(plaintext)

        assert isinstance(ciphertext, bytes)
        assert isinstance(nonce, bytes)
        assert len(nonce) == NONCE_SIZE
        assert ciphertext != plaintext.encode("utf-8")
        assert crypto.decrypt_text(ciphertext, nonce) == plaintext

    def test_encrypt_decrypt_roundtrip_bytes(self, crypto: MessageCrypto) -> None:
        payload = b"\x00\x01\xff binary payload"
        ciphertext, nonce = crypto.encrypt(payload)
        assert crypto.decrypt(ciphertext, nonce) == payload

    def test_each_encrypt_uses_unique_nonce(self, crypto: MessageCrypto) -> None:
        nonces = {crypto.encrypt("same")[1] for _ in range(32)}
        assert len(nonces) == 32

    def test_same_plaintext_yields_different_ciphertext(self, crypto: MessageCrypto) -> None:
        c1, _ = crypto.encrypt("same")
        c2, _ = crypto.encrypt("same")
        assert c1 != c2

    def test_tampered_ciphertext_raises(self, crypto: MessageCrypto) -> None:
        ciphertext, nonce = crypto.encrypt("secret")
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0x01
        with pytest.raises(DecryptionError):
            crypto.decrypt(bytes(tampered), nonce)

    def test_tampered_nonce_raises(self, crypto: MessageCrypto) -> None:
        ciphertext, nonce = crypto.encrypt("secret")
        bad_nonce = bytearray(nonce)
        bad_nonce[0] ^= 0x01
        with pytest.raises(DecryptionError):
            crypto.decrypt(ciphertext, bytes(bad_nonce))

    def test_wrong_key_raises(self, master_key: bytes) -> None:
        crypto_a = MessageCrypto(key_provider=StaticKeyProvider(master_key))
        crypto_b = MessageCrypto(key_provider=StaticKeyProvider(os.urandom(32)))
        ciphertext, nonce = crypto_a.encrypt("secret")
        with pytest.raises(DecryptionError):
            crypto_b.decrypt(ciphertext, nonce)

    def test_associated_data_must_match(self, crypto: MessageCrypto) -> None:
        ciphertext, nonce = crypto.encrypt(
            "secret", associated_data=b"chat:1"
        )
        assert crypto.decrypt(ciphertext, nonce, associated_data=b"chat:1") == b"secret"
        with pytest.raises(DecryptionError):
            crypto.decrypt(ciphertext, nonce, associated_data=b"chat:2")
        with pytest.raises(DecryptionError):
            crypto.decrypt(ciphertext, nonce)

    def test_invalid_nonce_length_raises(self, crypto: MessageCrypto) -> None:
        ciphertext, _ = crypto.encrypt("secret")
        with pytest.raises(DecryptionError):
            crypto.decrypt(ciphertext, b"short")

    def test_get_message_crypto_uses_env_key(self, master_key: bytes) -> None:
        encoded = base64.b64encode(master_key).decode()
        with override_settings(MESSAGE_ENCRYPTION_KEY=encoded):
            service = get_message_crypto()
            ciphertext, nonce = service.encrypt_text("via-env")
            assert service.decrypt_text(ciphertext, nonce) == "via-env"
