#!/usr/bin/env python3
"""
CLI for Secure QR Generator
Usage:
    python main.py encode --text "Hello" --out hello.png
    python main.py encode --infile secret.txt --out secret.png --key mysecret
    python main.py encode --text "Hello" --out hello.png --url "https://example.com/view"
    python main.py decode --img hello.png
    python main.py decode --img hello.png --key mysecret
"""
import argparse
import sys
import base64
from pathlib import Path

from qr_generator import generate_qr_from_text, generate_qr_from_file
from qr_verifier import decode_qr_image, verify_payload

def cmd_encode(args):
    if not args.text and not args.infile:
        print("Provide --text or --infile", file=sys.stderr)
        sys.exit(2)

    out_file = Path(args.out)
    if args.infile:
        infile = Path(args.infile)
        if not infile.exists():
            print("Input file not found:", infile, file=sys.stderr)
            sys.exit(2)
        generate_qr_from_file(infile, out_file, key=args.key, url=args.url)
    else:
        generate_qr_from_text(args.text, out_file, key=args.key, url=args.url)

def cmd_decode(args):
    img_path = Path(args.img)
    if not img_path.exists():
        print("Image file not found:", img_path, file=sys.stderr)
        sys.exit(2)

    try:
        payload = decode_qr_image(img_path)
    except Exception as e:
        print("Failed to decode QR:", e, file=sys.stderr)
        sys.exit(1)

    valid, message, meta, reason = verify_payload(payload, key=args.key)
    
    if valid:
        print("✅ Verification successful")
        if message:
            try:
                decoded = base64.b64decode(message, validate=True)
                decoded.decode('utf-8')
                print("Message:", message)
            except Exception:
                try:
                    decoded = base64.b64decode(message, validate=True)
                    Path('restored.bin').write_bytes(decoded)
                    print("Binary file restored to: restored.bin")
                except Exception:
                    print("Message:", message)
        if meta:
            print(f"Mode: {meta.get('mode')}, Time: {meta.get('ts')}")
    else:
        print("❌ Verification FAILED")
        if reason:
            print("Reason:", reason)

def main():
    parser = argparse.ArgumentParser(description="Secure QR Code Generator")
    sub = parser.add_subparsers(dest='cmd', required=True)

    enc = sub.add_parser('encode', help='Create secure QR from text or file')
    enc.add_argument('--text', help='Text to embed')
    enc.add_argument('--infile', help='File to embed')
    enc.add_argument('--out', default='secure_qr.png', help='Output filename')
    enc.add_argument('--key', help='Secret key for HMAC (optional)')
    enc.add_argument('--url', help='URL to embed payload in (optional)')

    dec = sub.add_parser('decode', help='Decode and verify QR')
    dec.add_argument('--img', required=True, help='QR image to decode')
    dec.add_argument('--key', help='Secret key if HMAC was used')

    args = parser.parse_args()
    if args.cmd == 'encode':
        cmd_encode(args)
    elif args.cmd == 'decode':
        cmd_decode(args)

if __name__ == '__main__':
    main()
