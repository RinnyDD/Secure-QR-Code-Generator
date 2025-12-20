"""QR generation and payload building."""

import os
import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import qrcode

from crypto_utils import compute_hash, compute_hmac


def _get_qrcode_assets_dir() -> Path:
    """Get/create assets/qrCode directory."""
    override = os.getenv("SECURE_QR_ASSETS_DIR")
    if override:
        assets_dir = Path(override)
        assets_dir.mkdir(parents=True, exist_ok=True)
        return assets_dir

    project_root = Path(__file__).resolve().parents[1]
    assets_dir = project_root / "assets" / "qrCode"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir


def _make_payload_bytes(message_bytes: bytes, key: str | None) -> str:
    """Create secure payload with hash/HMAC and return base64 string."""
    ts = datetime.now(timezone.utc).isoformat()
    if key:
        mac_b64 = base64.b64encode(compute_hmac(message_bytes, key)).decode("ascii")
        mode = "hmac"
    else:
        mac_b64 = compute_hash(message_bytes).hex()
        mode = "hash"

    payload = {
        "v": 1,
        "mode": mode,
        "mac": mac_b64,
        "msg_b64": base64.b64encode(message_bytes).decode("ascii"),
        "ts": ts,
    }
    j = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(j).decode("ascii")


def _embed_payload_in_url(url: str, payload_b64: str) -> str:
    """Add payload as 'data' query parameter to URL."""
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q["data"] = payload_b64
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))


def _generate_qr_img(data_str: str, out_path: Path) -> Path:
    """Create and save QR image."""
    out_path = Path(out_path)
    filename = out_path.name or "secure_qr.png"
    assets_dir = _get_qrcode_assets_dir()
    final_path = assets_dir / filename

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=6,
        border=2,
    )
    qr.add_data(data_str)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise RuntimeError(f"Payload too large for QR code: {e}")

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(final_path)
    return final_path


def generate_qr_from_text(
    text: str,
    out_path: Path,
    key: str | None = None,
    url: str | None = None,
):
    """Generate QR from text, save to assets/qrCode/."""
    payload_b64 = _make_payload_bytes(text.encode("utf-8"), key)
    data = _embed_payload_in_url(url, payload_b64) if url else payload_b64
    final = _generate_qr_img(data, out_path)
    print(f"Generated QR saved at: {final}")


def generate_qr_from_file(
    infile: Path,
    out_path: Path,
    key: str | None = None,
    url: str | None = None,
):
    """Generate QR from file bytes, save to assets/qrCode/."""
    with open(infile, "rb") as f:
        message_bytes = f.read()
    payload_b64 = _make_payload_bytes(message_bytes, key)
    data = _embed_payload_in_url(url, payload_b64) if url else payload_b64
    final = _generate_qr_img(data, out_path)
    print(f"Generated QR for file '{infile}' saved at: {final}")
