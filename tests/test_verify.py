import base64
import json

from qr_generator import _make_payload_bytes
from qr_verifier import verify_payload


def test_tamper_detection():
    payload_b64 = _make_payload_bytes(b"original", key=None)
    raw = base64.urlsafe_b64decode(payload_b64)
    j = json.loads(raw)
    j["msg_b64"] = base64.b64encode(b"tampered").decode("ascii")
    tampered = base64.urlsafe_b64encode(json.dumps(j).encode()).decode()
    valid, _, _, reason = verify_payload(tampered, key=None)
    assert not valid
    assert "mismatch" in reason.lower()
