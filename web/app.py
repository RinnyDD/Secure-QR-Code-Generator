# web/app.py
from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from pathlib import Path
import base64
import sys

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))
from qr_secure import decode_qr_image, verify_payload

app = Flask(__name__)
app.secret_key = "change-this-secret"

UPLOAD_DIR = Path(__file__).resolve().parent / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        file = request.files.get("qrfile")
        key = request.form.get("key") or None

        if not file:
            flash("Please choose an image file.", "error")
            return redirect(url_for("index"))

        # save uploaded file
        tmp_path = UPLOAD_DIR / file.filename
        file.save(tmp_path)

        try:
            payload = decode_qr_image(tmp_path)
        except Exception as e:
            # If the uploaded image contains no QR, show a friendly message
            msg = str(e)
            if 'No QR code found' in msg or 'No QR' in msg:
                result = {
                    "valid": False,
                    "message": None,
                    "meta": None,
                    "reason": "This is not the qrcode",
                    "is_file": False,
                    "download_name": None,
                }
                return render_template("index.html", result=result)
            # otherwise fall back to flashing the error
            flash(f"Failed to decode QR: {e}", "error")
            return redirect(url_for("index"))

        # verify payload (returns valid, message, meta, reason)
        valid, message, meta, reason = verify_payload(payload, key=key)

        # By default, do not expose restored file bytes unless verification succeeded
        is_file = False
        file_bytes = None
        download_name = None

        if valid:
            # Only attempt to decode/download when verification passed
            # If verify_payload returned a base64 string for binary, try decode it
            if isinstance(message, str):
                try:
                    decoded = base64.b64decode(message, validate=True)
                    # If bytes cannot be decoded to utf-8 cleanly, treat as binary file
                    try:
                        decoded.decode('utf-8')
                        # It's text; keep message as text
                    except Exception:
                        is_file = True
                        file_bytes = decoded
                except Exception:
                    # not base64, message is plain text
                    pass

            # If it's a file, save it for download
            if is_file and file_bytes:
                dp = UPLOAD_DIR / (file.filename + ".restored")
                dp.write_bytes(file_bytes)
                download_name = dp.name

        # If not valid, do NOT provide message content or downloads.
        safe_message = None if not valid else (message if not is_file else "(binary file - use download)")

        result = {
            "valid": valid,
            "message": safe_message,
            "meta": meta,
            "reason": reason,
            "is_file": is_file and valid,
            "download_name": download_name if valid else None,
        }

        return render_template("index.html", result=result)

    return render_template("index.html", result=None)

@app.route("/download/<path:name>")
def download(name):
    p = UPLOAD_DIR / name
    if not p.exists():
        flash("File not found.", "error")
        return redirect(url_for("index"))
    return send_file(str(p), as_attachment=True, download_name=name)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
