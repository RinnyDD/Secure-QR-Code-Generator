"""All tests for Secure QR Generator."""
import sys
import base64
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qr_secure import (compute_hash, compute_hmac, generate_qr_from_text, 
                       decode_qr_image, verify_payload, _make_payload_bytes)

def test_hash_length():
    d = compute_hash(b"hello")
    assert len(d) == 32  # SHA256 = 32 bytes

def test_hmac_different_keys():
    h1 = compute_hmac(b"msg", "key1")
    h2 = compute_hmac(b"msg", "key2")
    assert h1 != h2
   
def test_generate_and_verify(tmp_path):
    out = tmp_path / "test.png"
    generate_qr_from_text("test-message", out, key=None)
    payload = decode_qr_image(out)
    valid, message, meta, reason = verify_payload(payload, key=None)
    assert valid
    assert "test-message" in message

def test_tamper_detection():
    payload_b64 = _make_payload_bytes(b"original", key=None)
    raw = base64.urlsafe_b64decode(payload_b64)
    j = json.loads(raw)
    j['msg_b64'] = base64.b64encode(b"tampered").decode('ascii')
    tampered = base64.urlsafe_b64encode(json.dumps(j).encode()).decode()
    valid, _, _, reason = verify_payload(tampered, key=None)
    assert not valid
    assert "mismatch" in reason.lower()
