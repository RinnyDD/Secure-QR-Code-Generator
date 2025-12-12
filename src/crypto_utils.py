"""
crypto_utils.py
Small crypto helpers: SHA-256 hash and HMAC-SHA256.
Uses built-in hashlib and hmac (no external crypto library required).
"""
import hashlib
import hmac

def compute_hash(data: bytes) -> bytes:
    """Return SHA-256 digest bytes."""
    h = hashlib.sha256()
    h.update(data)
    return h.digest()

def compute_hmac(data: bytes, key: str) -> bytes:
    """Return HMAC-SHA256 bytes using the given secret key (utf-8)."""
    key_bytes = key.encode('utf-8')
    return hmac.new(key_bytes, data, hashlib.sha256).digest()
