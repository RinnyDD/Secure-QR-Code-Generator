"""Cryptographic helpers used across the project."""

import hashlib
import hmac


def compute_hash(data: bytes) -> bytes:
    """Return SHA-256 digest bytes."""
    return hashlib.sha256(data).digest()


def compute_hmac(data: bytes, key: str) -> bytes:
    """Return HMAC-SHA256 bytes using the given secret key."""
    return hmac.new(key.encode("utf-8"), data, hashlib.sha256).digest()
