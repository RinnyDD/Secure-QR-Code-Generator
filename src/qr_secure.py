"""
qr_secure.py - All-in-one secure QR code generation and verification.
Combines crypto, generation, and verification functions.
"""
import hashlib
import hmac
import json
import base64
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, parse_qs, parse_qsl, urlencode, urlunparse

import qrcode
from PIL import Image
from pyzbar.pyzbar import decode as qr_decode

# ============== CRYPTO HELPERS ==============

def compute_hash(data: bytes) -> bytes:
    """Return SHA-256 digest bytes."""
    return hashlib.sha256(data).digest()

def compute_hmac(data: bytes, key: str) -> bytes:
    """Return HMAC-SHA256 bytes using the given secret key."""
    return hmac.new(key.encode('utf-8'), data, hashlib.sha256).digest()

# ============== QR GENERATION ==============

def _get_qrcode_assets_dir() -> Path:
    """Get/create assets/qrCode directory."""
    project_root = Path(__file__).resolve().parents[1]
    assets_dir = project_root / "assets" / "qrCode"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir

def _make_payload_bytes(message_bytes: bytes, key: str | None) -> str:
    """Create secure payload with hash/HMAC and return base64 string."""
    ts = datetime.now(timezone.utc).isoformat()
    if key:
        mac_b64 = base64.b64encode(compute_hmac(message_bytes, key)).decode('ascii')
        mode = "hmac"
    else:
        mac_b64 = compute_hash(message_bytes).hex()
        mode = "hash"
    
    payload = {
        "v": 1, "mode": mode, "mac": mac_b64,
        "msg_b64": base64.b64encode(message_bytes).decode('ascii'),
        "ts": ts
    }
    j = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(j).decode('ascii')

def _embed_payload_in_url(url: str, payload_b64: str) -> str:
    """Add payload as 'data' query parameter to URL."""
    p = urlparse(url)
    q = dict(parse_qsl(p.query))
    q['data'] = payload_b64
    return urlunparse((p.scheme, p.netloc, p.path, p.params, urlencode(q), p.fragment))

def generate_qr_from_text(text: str, out_path: Path, key: str | None = None, url: str | None = None):
    """Generate QR from text, save to assets/qrCode/."""
    payload_b64 = _make_payload_bytes(text.encode('utf-8'), key)
    data = _embed_payload_in_url(url, payload_b64) if url else payload_b64
    final = _generate_qr_img(data, out_path)
    print(f"Generated QR saved at: {final}")

def generate_qr_from_file(infile: Path, out_path: Path, key: str | None = None, url: str | None = None):
    """Generate QR from file bytes, save to assets/qrCode/."""
    with open(infile, 'rb') as f:
        message_bytes = f.read()
    payload_b64 = _make_payload_bytes(message_bytes, key)
    data = _embed_payload_in_url(url, payload_b64) if url else payload_b64
    final = _generate_qr_img(data, out_path)
    print(f"Generated QR for file '{infile}' saved at: {final}")

def _generate_qr_img(data_str: str, out_path: Path) -> Path:
    """Create and save QR image."""
    out_path = Path(out_path)
    filename = out_path.name or "secure_qr.png"
    assets_dir = _get_qrcode_assets_dir()
    final_path = assets_dir / filename

    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_Q, box_size=6, border=2)
    qr.add_data(data_str)
    try:
        qr.make(fit=True)
    except ValueError as e:
        raise RuntimeError(f"Payload too large for QR code: {e}")
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(final_path)
    if out_path.parent.exists() and out_path != final_path:
        img.save(out_path)
    return final_path

# ============== QR VERIFICATION ==============

def decode_qr_image(img_path: Path) -> str:
    """Decode QR image and return payload string."""
    img = Image.open(img_path)
    decoded = qr_decode(img)
    if not decoded:
        raise RuntimeError("No QR code found in image.")
    raw = decoded[0].data.decode('utf-8')
    
    # Extract payload from URL if present
    try:
        p = urlparse(raw)
        if p.scheme in ('http', 'https'):
            qs = parse_qs(p.query)
            if 'data' in qs:
                return qs['data'][0]
    except Exception:
        pass
    return raw

def verify_payload(payload_b64: str, key: str | None = None):
    """
    Verify payload integrity.
    Returns: (valid: bool, message: str|None, meta: dict|None, reason: str|None)
    """
    try:
        j = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(j)
    except Exception as e:
        return False, None, None, f"Invalid payload: {e}"

    mode = payload.get('mode')
    mac_field = payload.get('mac')
    msg_b64 = payload.get('msg_b64')
    ts = payload.get('ts')

    if not all([mode, mac_field, msg_b64]):
        return False, None, None, "Missing fields in payload"

    try:
        message_bytes = base64.b64decode(msg_b64)
    except Exception as e:
        return False, None, None, f"Message decode failed: {e}"

    meta = {"mode": mode, "ts": ts}
    
    # Try to decode message as text
    try:
        message = message_bytes.decode('utf-8')
    except Exception:
        message = base64.b64encode(message_bytes).decode('ascii')

    # Verify integrity
    if mode == 'hmac':
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
    
    elif mode == 'hash':
        expected_hex = compute_hash(message_bytes).hex()
        if expected_hex == mac_field:
            return True, message, meta, None
        return False, message, meta, "Hash mismatch - content tampered"
    
    return False, None, None, f"Unknown mode: {mode}"
