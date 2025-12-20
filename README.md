# Secure QR Code Generator

Simple tool to create and verify secure QR payloads.

This project can pack text or small files into a QR image and verify the QR payload.

## Features
- Encode text or a small file into a QR image.
- Verify QR payloads and check integrity (HMAC or SHA-256).
- Optional URL embedding: QR can open a website and carry the payload as a `data` query parameter.
- CLI and a simple web UI to upload and verify QR images.
- If a verified payload is a binary file, the tool saves a restored file.

## Limitations
- QR codes have size limits. Large images or big files may not fit in one QR.
- Do not expect to store multi-megabyte files in a single QR.

## Install
Open PowerShell and run:

```powershell
python -m pip install -r requirements.txt
```

## Run the web UI
Start the web app and open http://localhost:5000 in your browser.

```powershell
python web\app.py
```

Optional (recommended): set a Flask secret key via environment variable:

```powershell
$env:FLASK_SECRET_KEY = "some-random-string"
python web\app.py
```

The web page lets you upload a QR image and enter the optional HMAC key.
If the QR is valid and contains a binary file, a download link appears.

## Project structure (short)
- Core logic (generate + verify) is in `src\qr_secure.py`.
- CLI entrypoint is `src\main.py`.
- Web UI is `web\app.py` with template in `web\templates\index.html`.

## Libraries
- Python libraries are listed in `requirements.txt`.
- If you use `pipenv` or `poetry`, lock files are `Pipfile.lock` or `poetry.lock`.
- Do not commit virtual environments or library folders (for example: `venv/`, `.venv/`, `site-packages/`, `vendor/`). These are ignored by `.gitignore`.

## CLI usage
The CLI script is `src\main.py`.

Encode examples:

```powershell
# encode simple text to a PNG
python src/main.py encode --text "Hello world" --out hello.png

# encode a small file (txt/pdf) into a QR
python src/main.py encode --infile secret.txt --out secret_qr.png

# encode with a secret key (HMAC)
python src/main.py encode --text "secret" --out myqr.png --key mysecret

# encode and embed payload into a clickable URL
# (scanning with a phone opens the URL; your verifier extracts `data=...`)
python src/main.py encode --text "Hello" --out link.png --key mysecret --url "https://example.com/view"
```

Decode / verify example:

```powershell
python src/main.py decode --img secret_qr.png

# if the QR used an HMAC key:
python src/main.py decode --img secret_qr.png --key mysecret
```

Notes:
- Generated QR images are copied to `assets\qrCode\`.
- If the verified payload is binary, the CLI writes `restored.bin` in the current folder.

## Tests
Run tests from the project root:

```powershell
python -m pytest -q
```

## Troubleshooting
- If you see an error about payload size, the data is too large for a single QR. Use a smaller file or shorter text.
- If the web UI says "This is not the qrcode", the uploaded image has no QR code or pyzbar could not detect it.

## Security notes
- If you use `--key`, HMAC is used to protect integrity. Keep keys secret.
- The app is for demo use. Do not run the web UI in production without changing secrets and adding real security.

## Note 
This project focuses on integrity verification rather than data confidentiality. 
Encryption is intentionally excluded to keep the system simple and aligned with project scope.
