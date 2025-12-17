"""
qr_verify.py
Decode QR images and verify payload integrity (HMAC or SHA256).
"""
import json
import base64
from pathlib import Path

from pyzbar.pyzbar import decode as qr_decode
from PIL import Image
from urllib.parse import urlparse, parse_qs
    
from crypto_utils import compute_hash, compute_hmac

def decode_qr_image(img_path: Path) -> str:
    img = Image.open(img_path)
    decoded = qr_decode(img)
    if not decoded:
        raise RuntimeError("No QR code found in image.")
    # Use the first QR payload
    raw = decoded[0].data.decode('utf-8')
    # If the QR contains a URL with our payload in a query parameter (e.g. ?data=...)
    # extract and return just the payload. Otherwise return the raw string.
    try:
        p = urlparse(raw)
        if p.scheme in ('http', 'https'):
            qs = parse_qs(p.query)
            if 'data' in qs and qs['data']:
                return qs['data'][0]
    except Exception:
        pass
    return raw

def verify_payload(payload_b64: str, key: str | None = None):
    """
    Returns (valid:bool, message:str|None, meta:dict|None, reason:str|None)
    message is bytes decoded to utf-8 if possible, otherwise b64 string.
    """
    try:
        j = base64.urlsafe_b64decode(payload_b64)
        payload = json.loads(j)
    except Exception as e:
        return False, None, None, f"invalid payload encoding: {e}"

    # basic fields
    mode = payload.get('mode')
    mac_field = payload.get('mac')
    msg_b64 = payload.get('msg_b64')
    ts = payload.get('ts')

    if not (mode and mac_field and msg_b64):
        return False, None, None, "missing fields in payload"

    try:
        message_bytes = base64.b64decode(msg_b64)
    except Exception as e:
        return False, None, None, f"message b64 decode failed: {e}"

    # verify
    if mode == 'hmac':
        if not key:
            return False, None, None, "HMAC was used to create QR — a secret key is required for verification"
        expected = compute_hmac(message_bytes, key)
        try:
            import binascii
            provided = base64.b64decode(mac_field)
        except Exception:
            return False, None, None, "Invalid HMAC field encoding"
        if expected == provided:
            # try decode message as utf-8 for user-friendly output
            try:
                return True, message_bytes.decode('utf-8'), {"mode": mode, "ts": ts}, None
            except Exception:
                return True, base64.b64encode(message_bytes).decode('ascii'), {"mode": mode, "ts": ts}, None
        else:
            # mismatch
            try:
                return False, message_bytes.decode('utf-8'), {"mode": mode, "ts": ts}, "HMAC mismatch - content was changed or wrong key"
            except Exception:
                return False, base64.b64encode(message_bytes).decode('ascii'), {"mode": mode, "ts": ts}, "HMAC mismatch - content was changed or wrong key"

    elif mode == 'hash':
        expected_hex = compute_hash(message_bytes).hex()
        if expected_hex == mac_field:
            try:
                return True, message_bytes.decode('utf-8'), {"mode": mode, "ts": ts}, None
            except Exception:
                return True, base64.b64encode(message_bytes).decode('ascii'), {"mode": mode, "ts": ts}, None
        else:
            try:
                return False, message_bytes.decode('utf-8'), {"mode": mode, "ts": ts}, "Hash mismatch - content was changed"
            except Exception:
                return False, base64.b64encode(message_bytes).decode('ascii'), {"mode": mode, "ts": ts}, "Hash mismatch - content was changed"
    else:
        return False, None, None, f"unknown mode: {mode}"
