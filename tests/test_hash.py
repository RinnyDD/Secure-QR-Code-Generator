from crypto_utils import compute_hash, compute_hmac


def test_hash_length():
    d = compute_hash(b"hello")
    assert len(d) == 32  # SHA256 = 32 bytes


def test_hmac_different_keys():
    h1 = compute_hmac(b"msg", "key1")
    h2 = compute_hmac(b"msg", "key2")
    assert h1 != h2
