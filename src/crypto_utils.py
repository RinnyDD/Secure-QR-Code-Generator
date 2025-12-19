"""
crypto_utils.py
Small crypto helpers: SHA-256 hash and HMAC-SHA256.
Uses built-in hashlib and hmac (no external crypto library required).
"""
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet

def compute_hash(data: bytes) -> bytes:
    """Return SHA-256 digest bytes."""
    h = hashlib.sha256()
    h.update(data)
    return h.digest()

def compute_hmac(data: bytes, key: str) -> bytes:
    """Return HMAC-SHA256 bytes using the given secret key (utf-8)."""
    key_bytes = key.encode('utf-8')
    return hmac.new(key_bytes, data, hashlib.sha256).digest()

# def _derive_fernet_key(password: str) -> bytes:
#     """
#     Derive a Fernet-compatible key from a password.
#     (SHA-256 -> base64-url)
#     """
#     digest = hashlib.sha256(password.encode("utf-8")).digest()
#     return base64.urlsafe_b64encode(digest)

# def encrypt_bytes(data: bytes, password: str) -> bytes:
#     """
#     Encrypt data using Fernet (AES + HMAC).
#     """
#     f = Fernet(_derive_fernet_key(password))
#     return f.encrypt(data)

# def decrypt_bytes(token: bytes, password: str) -> bytes:
#     """
#     Decrypt Fernet token.
#     Raises exception if authentication fails.
#     """
#     f = Fernet(_derive_fernet_key(password))
#     return f.decrypt(token)