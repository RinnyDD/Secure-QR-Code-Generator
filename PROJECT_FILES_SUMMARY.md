Project: Secure-QR-Code-Generator

This document summarizes the repository files, explains how each file works, and provides usage and security notes.

**Project Purpose**
- Create secure QR codes that embed a compact JSON payload (either HMAC-protected or SHA-256 hashed) and provide tools to generate and verify them via CLI and a simple web UI.

**Payload format**
- Base64-url encoded JSON with fields: {
  "v":1,
  "mode":"hmac"|"hash",
  "mac":"...",
  "msg_b64":"...",
  "ts":"ISO"
}
- mode=hmac: `mac` is base64(HMAC-SHA256(message, key)).
- mode=hash: `mac` is hex(SHA256(message)).

---

**Top-level files**
- `README.md` : Project description and usage instructions.
- `requirements.txt` : Python packages to install for running and testing.
- `LICENSE` : Project license.

**src/**
- `crypto_utils.py`
  - compute_hash(data: bytes) -> bytes : returns SHA-256 digest bytes.
  - compute_hmac(data: bytes, key: str) -> bytes : returns HMAC-SHA256 bytes (key is UTF-8 encoded).

- `utils.py`
  - read_file_bytes(path: Path) -> bytes : reads and returns file bytes.
  - ensure_parent_dir(path: Path) : creates parent directory if missing.

- `qr_generator.py`
  - Purpose: Build secure payloads, optionally embed them in a clickable URL, and generate QR images.
  - Key functions:
    - `_get_qrcode_assets_dir()` : returns/creates `<project_root>/assets/qrCode`.
    - `_make_payload_bytes(message_bytes, key)` : builds JSON payload and returns base64-url encoded string.
    - `_embed_payload_in_url(url, payload_b64, param_name='data')` : returns URL with `?data=<payload>` merged with existing query params.
    - `generate_qr_from_text(text, out_path, key=None, url=None)` : generates QR from text; if `url` provided, QR encodes the URL carrying the payload in `data` parameter.
    - `generate_qr_from_file(infile, out_path, key=None, url=None)` : same as above but reads binary file and embeds its bytes.
    - `_generate_qr_img(data_str, out_path)` : generates PNG using `qrcode` and saves it. If `out_path` parent exists (e.g., a tmp dir), saves there; otherwise saves to assets/qrCode for project organization.
  - Notes: Error correction Q, box_size=6, border=2. Embedding in URLs may create long URLs (watch QR capacity).

- `qr_verify.py`
  - Purpose: Decode QR images and verify payload integrity.
  - Key functions:
    - `decode_qr_image(img_path)` : opens image, decodes QR payload using `pyzbar`. If the decoded string is an `http`/`https` URL and contains a `data` query parameter, it returns that parameter value (the payload); otherwise returns raw decoded string.
    - `verify_payload(payload_b64, key=None)` : base64-url-decodes payload, parses JSON, decodes `msg_b64`, and verifies either HMAC or SHA-256 hash.
      - Returns `(valid:bool, message:str|None, meta:dict|None, reason:str|None)`.
      - For binary messages, `message` may be returned as a base64 string; caller may attempt to decode it to bytes.
  - Security note: uses equality to compare HMAC bytes. Consider using `hmac.compare_digest` to avoid timing attacks.

- `main.py` (CLI)
  - `encode` subcommand: `--text` or `--infile`, `--out`, `--key`. Calls generator functions.
  - `decode` subcommand: `--img`, `--key`. Calls `decode_qr_image` and `verify_payload` and prints results.

**web/**
- `web/app.py` : Small Flask app to upload a QR image and verify it.
  - Adds `src/` to `sys.path` so `qr_verify` can be imported.
  - Uploads saved to `web/uploads/`.
  - POST `/` accepts `qrfile` and optional `key`, decodes and verifies payload, and if verification succeeded and the message decodes to binary, writes a restored file for download.
  - GET `/download/<name>` serves restored files for download.
  - Note: `app.secret_key` is a placeholder; do not use in production as-is. No file size limits or sanitization.

- `web/templates/index.html` : Simple UI for file upload, key input, and displaying verification result and metadata.

**tests/**
- `test_hash.py` : tests for `compute_hash` length and that HMAC changes with different keys.
- `test_generate.py` : tests encode->decode->verify flow using `tmp_path`. The generator was adjusted so saving to a provided tmp path works.
- `test_verify.py` : tests tamper detection by altering payload JSON and verifying the mismatch is detected.

**assets/qrCode/**
- Example QR PNGs created by the project. These are output artifacts and used for demonstrations.

---

**How the system operates (data flow)**
1. Encoding
   - Message bytes are packed into a JSON payload with metadata and either an HMAC or SHA-256 digest.
   - Optionally the base64 payload is embedded into a URL as `?data=<payload>`.
   - The string (payload or URL) is encoded into a QR image and saved to disk.

2. Decoding/Verification
   - QR image is decoded. If it contains a URL with `data` param, the `data` value is extracted.
   - The payload is base64-url-decoded and parsed. The original message bytes are recovered from `msg_b64`.
   - HMAC or hash is verified. Result (valid/invalid), message, metadata and reason are returned.

**Common commands**
- Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

- Run tests (ensure `src` is importable):

```powershell
$env:PYTHONPATH = "src"; python -m pytest -q
```

- CLI encode example:

```powershell
python src\main.py encode --text "hello" --out hello.png
# with HMAC key
python src\main.py encode --text "secret" --out secret.png --key mysecret
# programmatically (url embedding):
# generate_qr_from_text("secret", Path("hello.png"), key=None, url="https://example.com/view")
```

You can now embed a clickable website URL into the QR so that phone scanners open the site while the secure payload remains hidden in a `data` query parameter. Example CLI usage:

```powershell
python src\main.py encode --text "secret message" --out myqr.png --url "https://example.com/view"
```
This encodes `https://example.com/view?data=<payload>` in the QR; ordinary phone scanners will navigate to that URL, while your verification tools extract and validate the hidden payload.

- CLI decode/verify example:

```powershell
python src\main.py decode --img path\to\qr.png
python src\main.py decode --img path\to\qr.png --key mysecret
```

- Run web UI:

```powershell
python web\app.py
# open http://127.0.0.1:5000/
```

**Security & reliability notes and suggestions**
- Use `hmac.compare_digest` for HMAC comparisons to reduce timing attack risk.
- Keep payloads small (QR capacity limited). Consider storing large files remotely and embedding a short URL/ID instead.
- Use HTTPS for URLs carrying payloads; URLs may be logged or leaked by user agents or intermediaries.
- Implement file size limits and sanitization for uploads in `web/app.py` and do not use the placeholder `app.secret_key` in production.
- Consider packaging the project (e.g., `pip install -e .`) to avoid needing `PYTHONPATH` in tests and scripts.

**Next steps (optional)**
- Add `--url` flag to `main.py` encode CLI so URL embedding is exposed via CLI.
- Replace equality check with `hmac.compare_digest` in `qr_verify.py`.
- Make the query parameter name configurable instead of using `data`.
- Add compression or remote storage for larger payloads.

Note: the `--url` flag was implemented and is available in the CLI. If you want the query parameter name changed from `data` or made configurable, I can implement that next.

---

Generated file: `PROJECT_FILES_SUMMARY.md` (project root)

If you want the summary in a different filename or folder (e.g., `docs/`), tell me and I will move it there.
