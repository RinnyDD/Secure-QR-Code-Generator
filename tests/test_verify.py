import base64
import json
from qr_generator import _make_payload_bytes
from qr_verify import verify_payload

def test_tamper_detection():
    # create payload with no key (hash mode)
    msg = b"original"
    payload_b64 = _make_payload_bytes(msg, key=None)
    # decode and alter payload JSON
    raw = base64.urlsafe_b64decode(payload_b64)
    j = json.loads(raw)
    j['msg_b64'] = base64.b64encode(b"tampered").decode('ascii')
    tampered = base64.urlsafe_b64encode(json.dumps(j, separators=(',', ':')).encode('utf-8')).decode('ascii')
    valid, message, meta, reason = verify_payload(tampered, key=None)
    assert not valid
    assert "Hash mismatch" in reason or "mismatch" in reason.lower()
