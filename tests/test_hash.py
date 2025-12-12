import base64
from pathlib import Path
from crypto_utils import compute_hash, compute_hmac

def test_hash_length():
    d = compute_hash(b"hello")
    assert isinstance(d, (bytes, bytearray))
    assert len(d) == 32  # SHA256 = 32 bytes

def test_hmac_diff_keys():
    m = b"message"
    k1 = "a"
    k2 = "b"
    h1 = compute_hmac(m, k1)
    h2 = compute_hmac(m, k2)
    assert h1 != h2
