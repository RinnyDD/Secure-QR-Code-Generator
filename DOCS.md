# Secure QR Code Generator — Documentation

This document explains how the project works (crypto design, QR payload format, CLI + web flow) and how each file fits together.

## 1) What this project does
The project generates QR codes that **carry a signed payload**. When you decode the QR using this project, it verifies whether the payload was modified.

- **Integrity** means: you can detect if the message was changed.
- This project does **not** encrypt data. Anyone who decodes the QR can still read the message bytes (or the base64 form for binary). The security goal here is *tamper detection*, not confidentiality.

## 2) Two integrity modes
When creating a QR, you choose one of two modes automatically:

### Mode A: `hash` (no key)
- Stored integrity value: `SHA-256(message)`
- Pros: simple, no secret needed
- Cons: not “authenticated” — an attacker can replace the message and recompute SHA-256.

### Mode B: `hmac` (with key)
- Stored integrity value: `HMAC-SHA256(message, key)`
- Pros: authenticated integrity — attacker cannot forge without the key
- Cons: you must remember and provide the key for verification.

In practice, **use `--key` (HMAC mode)** for the “secure” version.

## 3) Payload format (what is inside the QR)
The QR stores a **base64-url encoded JSON** structure.

### 3.1 JSON fields
Example structure (not real values):

```json
{
  "v": 1,
  "mode": "hmac",
  "mac": "...",
  "msg_b64": "...",
  "ts": "2025-12-20T12:34:56.789+00:00"
}
```

Field meaning:
- `v`: payload version (for future format changes)
- `mode`: `"hash"` or `"hmac"`
- `mac`:
  - if `mode="hash"`: hex string of SHA-256 digest
  - if `mode="hmac"`: base64 of the HMAC bytes
- `msg_b64`: base64 of the original message bytes
- `ts`: timestamp (metadata only)

### 3.2 Why base64-url?
After JSON is created, it is encoded using `base64.urlsafe_b64encode(...)` so the payload string:
- is safe to put in a QR
- is safe to embed into a URL query param (`?data=...`) without breaking characters

## 4) URL embedding (optional)
If you provide a URL, the QR does NOT store the raw payload alone. Instead it stores:

```
https://example.com/view?data=<payload>
```

- Phone QR scanners will usually open the URL in the browser.
- Your verifier extracts the `data` parameter and verifies it.

## 5) End-to-end workflow

### 5.1 Encoding
1. Read input (text or file bytes)
2. Build payload:
   - compute `mac` using SHA-256 (hash mode) or HMAC-SHA256 (hmac mode)
   - base64-encode message bytes to `msg_b64`
   - add timestamp `ts`
3. JSON → base64-url string
4. Optionally wrap payload into URL (`?data=...`)
5. Create QR image and save it

### 5.2 Decoding + verification
1. Decode QR image to get a string
2. If it’s a URL, extract `data` parameter
3. base64-url decode → JSON
4. base64 decode `msg_b64` to original message bytes
5. Recompute expected `mac`
6. Compare expected vs provided
7. Return:
   - `valid=True/False`
   - the decoded message
   - metadata (mode + timestamp)
   - a reason if invalid

## 6) File-by-file explanation

### 6.1 `src/qr_secure.py` (core library)
This file contains **all** core logic.

#### A) Crypto helpers
- `compute_hash(data: bytes) -> bytes`
  - Uses `hashlib.sha256(data).digest()`
  - Output is always 32 bytes.

- `compute_hmac(data: bytes, key: str) -> bytes`
  - Uses `hmac.new(key_bytes, data, hashlib.sha256).digest()`
  - Output is also 32 bytes.

#### B) Payload creation
- `_make_payload_bytes(message_bytes: bytes, key: str | None) -> str`
  - Creates timestamp in UTC.
  - If `key` exists → `mode="hmac"` and `mac=base64(hmac_bytes)`
  - If no `key` → `mode="hash"` and `mac=sha256_hex`
  - Builds JSON payload and returns `base64url(JSON)`.

#### C) URL embedding
- `_embed_payload_in_url(url: str, payload_b64: str) -> str`
  - Parses URL, merges/overwrites query parameter `data`, rebuilds URL.

#### D) QR generation
- `_get_qrcode_assets_dir() -> Path`
  - Ensures `assets/qrCode/` exists.

- `generate_qr_from_text(text, out_path, key=None, url=None)`
  - Converts text to bytes and calls `_make_payload_bytes`.

- `generate_qr_from_file(infile, out_path, key=None, url=None)`
  - Reads file bytes and calls `_make_payload_bytes`.

- `_generate_qr_img(data_str, out_path) -> Path`
  - Builds the QR using `qrcode.QRCode(...ERROR_CORRECT_Q...)`
  - Saves canonical output to `assets/qrCode/<filename>`.
  - If `out_path` points to an existing directory, also saves there.

#### E) QR decoding + verification
- `decode_qr_image(img_path) -> str`
  - Uses `pyzbar` to extract QR data.
  - If QR data is `http/https` and has `data=...`, returns that `data` value.

- `verify_payload(payload_b64, key=None)`
  - Decodes payload, checks required fields.
  - Recomputes SHA-256 or HMAC.
  - Returns `(valid, message, meta, reason)`.
  - If message bytes are not valid UTF-8, it returns a base64 string so callers can rebuild binary.

---

### 6.2 `src/main.py` (CLI)
This file is the command-line entrypoint.

Commands:
- `encode`:
  - Requires either `--text` or `--infile`
  - Optional `--key` (enables HMAC mode)
  - Optional `--url` (wrap payload into a clickable URL)

- `decode`:
  - Requires `--img`
  - Optional `--key` (needed if QR was generated with `--key`)

Behavior details:
- `cmd_encode(args)` chooses whether to call `generate_qr_from_text` or `generate_qr_from_file`.
- `cmd_decode(args)` calls `decode_qr_image` then `verify_payload`.
- If verification succeeds and output looks like base64 for binary bytes, it writes `restored.bin`.

---

### 6.3 `web/app.py` (Flask server)
Provides a browser-based verifier.

Routes:
- `/` (GET): show upload form
- `/` (POST):
  - save uploaded file into `web/uploads/`
  - decode QR
  - verify payload
  - if valid and payload is binary, save a restored file and show a download link

- `/download/<name>`:
  - serves restored files from `web/uploads/`

Important note:
- `app.secret_key` is set to a placeholder string. For a school project that’s fine.

---

### 6.4 `web/templates/index.html` (UI page)
- HTML form uploads a QR image and optional key.
- Shows “Valid/Invalid” result.
- If payload is a binary file, it shows a “Download restored file” link.
- Adds `state-valid` or `state-invalid` class to `<body>` so CSS can color the background.

---

### 6.5 `web/static/style.css` (styling)
- Provides layout and colors.
- Uses `body.state-valid` and `body.state-invalid` to change background.
- Does not affect crypto; UI-only.

---

### 6.6 `tests/test_all.py` (tests)
Runs 4 checks:
- SHA-256 output length
- HMAC differs for different keys
- end-to-end: encode → decode → verify
- tamper detection: modify payload JSON and verify fails

## 7) How to run

### Install
```powershell
python -m pip install -r requirements.txt
```

### CLI examples
```powershell
# Text → QR
python src/main.py encode --text "Hello" --out hello.png

# File → QR
python src/main.py encode --infile secret.txt --out secret.png

# HMAC integrity (recommended)
python src/main.py encode --text "secret" --out secret.png --key mysecret

# URL embedding (phone opens URL)
python src/main.py encode --text "Hello" --out link.png --key mysecret --url "https://example.com/view"

# Verify
python src/main.py decode --img link.png --key mysecret
```

### Web UI
```powershell
python web/app.py
```
Open: http://127.0.0.1:5000/

### Tests
```powershell
python -m pytest -q
```

## 8) Common problems
- **“No QR code found in image.”**: image doesn’t contain a readable QR, or it’s too blurry.
- **Payload too large**: QR capacity is limited; URL embedding or smaller input helps.
- **HMAC key required**: if QR was created with `--key`, you must verify with the same key.

## 9) Security notes (school-level)
- SHA-256 mode detects changes but does not prevent forgery (attacker can recompute hash).
- HMAC mode prevents forgery without the secret key.
- Data is not encrypted; treat QR content as public.
