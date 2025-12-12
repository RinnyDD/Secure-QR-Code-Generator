from pathlib import Path
from qr_generator import generate_qr_from_text
from qr_verify import decode_qr_image, verify_payload

def test_generate_and_verify(tmp_path):
    out = tmp_path / "test.png"
    text = "unit-test-message"
    generate_qr_from_text(text, out, key=None)
    payload = decode_qr_image(out)
    valid, message, meta, reason = verify_payload(payload, key=None)
    assert valid
    assert "unit-test-message" in message
