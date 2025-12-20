from pathlib import Path

from qr_generator import generate_qr_from_text
from qr_verifier import decode_qr_image, verify_payload


def test_generate_and_verify(tmp_path: Path, monkeypatch):
    assets_dir = tmp_path / "qrCode"
    monkeypatch.setenv("SECURE_QR_ASSETS_DIR", str(assets_dir))

    out = tmp_path / "test.png"  # filename is used; directory is ignored
    generate_qr_from_text("test-message", out, key=None)

    saved = assets_dir / "test.png"
    payload = decode_qr_image(saved)
    valid, message, meta, reason = verify_payload(payload, key=None)
    assert valid
    assert "test-message" in message
