"""
qr_generator.py
Functions to create a secure payload and generate a QR image.
Now always saves generated QR images to: <project_root>/assets/qrCode/<filename>
Payload format is a small JSON (then base64-url encoded) containing:
  { "v":1, "mode":"hmac"|"hash", "mac": "...", "msg_b64": "...", "ts": "ISO" }
If key is provided, mode=hmac; otherwise mode=hash (SHA256).
"""
import json
import base64
from datetime import datetime, timezone
from pathlib import Path

import qrcode
from PIL import Image

from crypto_utils import compute_hash, compute_hmac
from utils import read_file_bytes

# --- helper to locate assets/qrCode in project root ---
def _get_qrcode_assets_dir() -> Path:
    # file is in project/src/qr_generator.py -> project root is two parents up
    project_root = Path(__file__).resolve().parents[1]
    assets_dir = project_root / "assets" / "qrCode"
    assets_dir.mkdir(parents=True, exist_ok=True)
    return assets_dir

def _make_payload_bytes(message_bytes: bytes, key: str | None):
    ts = datetime.now(timezone.utc).isoformat()
    if key:
        mode = "hmac"
        mac = compute_hmac(message_bytes, key)
        mac_b64 = base64.b64encode(mac).decode('ascii')
    else:
        mode = "hash"
        digest = compute_hash(message_bytes)
        mac_b64 = digest.hex()  # hex is concise for SHA256
    payload = {
        "v": 1,
        "mode": mode,
        "mac": mac_b64,
        "msg_b64": base64.b64encode(message_bytes).decode('ascii'),
        "ts": ts
    }
    j = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return base64.urlsafe_b64encode(j).decode('ascii')

def generate_qr_from_text(text: str, out_path: Path, key: str | None = None):
    """
    out_path can be a filename (hello.png) or a Path.
    The final file will be saved to: <project_root>/assets/qrCode/<out_path.name>
    """
    message_bytes = text.encode('utf-8')
    payload_b64 = _make_payload_bytes(message_bytes, key)
    final = _generate_qr_img(payload_b64, out_path)
    print(f"Generated QR saved at: {final}")

def generate_qr_from_file(infile: Path, out_path: Path, key: str | None = None):
    """
    Read binary file and embed its bytes into the QR payload.
    The output is saved to assets/qrCode/<out_path.name>
    """
    message_bytes = read_file_bytes(infile)
    payload_b64 = _make_payload_bytes(message_bytes, key)
    final = _generate_qr_img(payload_b64, out_path)
    print(f"Generated QR for file '{infile}' saved at: {final}")

def _generate_qr_img(data_str: str, out_path: Path) -> Path:
    """
    Create QR image from data_str and save into assets/qrCode/<filename>.
    Returns final Path.
    """
    # determine filename from out_path (if out_path is string or Path)
    out_path = Path(out_path)
    filename = out_path.name if out_path.name else "secure_qr.png"
    assets_dir = _get_qrcode_assets_dir()
    final_path = assets_dir / filename

    # generate QR
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=6,
        border=2
    )
    qr.add_data(data_str)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(final_path)
    return final_path
