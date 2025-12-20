"""QR decoding and payload verification."""

import base64
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from PIL import Image
from pyzbar.pyzbar import decode as qr_decode

from crypto_utils import compute_hash, compute_hmac


def decode_qr_image(img_path: Path) -> str:
    """Decode QR image and return payload string."""
    img = Image.open(img_path)
    decoded = qr_decode(img)
    if not decoded:
        raise RuntimeError("No QR code found in image.")
    raw = decoded[0].data.decode("utf-8")

    # Extract payload from URL if present
    try:
        p = urlparse(raw)
        if p.scheme in ("http", "https"):
            qs = parse_qs(p.query)
            if "data" in qs:
                return qs["data"][0]
    except Exception:
        pass
    return raw


def verify_payload(payload_b64: str, key: str | None = None):
    """Verify payload integrity.

    Returns: (valid: bool, message: str|None, meta: dict|None, reason: str|None)
    """
    try:
        j = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(j)
    except Exception as e:
        return False, None, None, f"Invalid payload: {e}"

    mode = payload.get("mode")
    mac_field = payload.get("mac")
    msg_b64 = payload.get("msg_b64")
    ts = payload.get("ts")

    if not all([mode, mac_field, msg_b64]):
        return False, None, None, "Missing fields in payload"

    try:
        message_bytes = base64.b64decode(msg_b64)
    except Exception as e:
        return False, None, None, f"Message decode failed: {e}"

    meta = {"mode": mode, "ts": ts}

    # Try to decode message as text
    try:
        message = message_bytes.decode("utf-8")
    except Exception:
        message = base64.b64encode(message_bytes).decode("ascii")

    # Verify integrity
    if mode == "hmac":
        if not key:
            return False, None, None, "HMAC key required for verification"
        expected = compute_hmac(message_bytes, key)
        try:
            provided = base64.b64decode(mac_field)
        except Exception:
            return False, None, None, "Invalid HMAC encoding"
        if expected == provided:
            return True, message, meta, None
        return False, message, meta, "HMAC mismatch - wrong key or tampered"

    if mode == "hash":
        expected_hex = compute_hash(message_bytes).hex()
        if expected_hex == mac_field:
            return True, message, meta, None
        return False, message, meta, "Hash mismatch - content tampered"

    return False, None, None, f"Unknown mode: {mode}"
