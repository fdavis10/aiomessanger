"""Encryption-layer exceptions.

Keep these distinct from Django/DRF errors so callers can map them to 4xx/5xx
without leaking crypto details into generic exception handlers.
"""


class CryptoError(Exception):
    """Base class for encryption/decryption failures."""


class EncryptionKeyError(CryptoError):
    """Master key missing, malformed, or wrong length."""


class DecryptionError(CryptoError):
    """Ciphertext could not be authenticated or decrypted (tamper / wrong key)."""
