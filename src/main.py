#!/usr/bin/env python3
"""
Main CLI for Secure QR Generator
Usage examples:
  python main.py encode --text "Hello" --out hello.png
  python main.py encode --infile secret.txt --out secret.png --key mysecret
  python main.py decode --img hello.png
  python main.py decode --img secret.png --key mysecret
"""
import argparse
import sys
from pathlib import Path

from qr_generator import generate_qr_from_text, generate_qr_from_file
from qr_verify import decode_qr_image, verify_payload

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
        generate_qr_from_file(infile, out_file, key=args.key)
    else:
        generate_qr_from_text(args.text, out_file, key=args.key)

def cmd_decode(args):
    img_path = Path(args.img)
    if not img_path.exists():
        print("Image file not found:", img_path, file=sys.stderr)
        sys.exit(2)

    try:
        payload = decode_qr_image(img_path)
    except Exception as e:
        print("Failed to decode QR image:", e, file=sys.stderr)
        sys.exit(1)

    valid, message, meta, reason = verify_payload(payload, key=args.key)
    if valid:
        print("✅ Verification successful — message is valid.")
        if meta:
            print("Message:")
        print(message)
        if meta:
            print("\nMetadata:")
            for k, v in meta.items():
                print(f"  {k}: {v}")
    else:
        print("❌ Verification FAILED.")
        if reason:
            print("Reason:", reason)
        # if partial message available, still show it
        if message is not None:
            print("\nDecoded message (may be tampered):")
            print(message)

def main():
    parser = argparse.ArgumentParser(description="Secure QR Code Generator (encode/decode)")
    sub = parser.add_subparsers(dest='cmd', required=True)

    enc = sub.add_parser('encode', help='Encrypt/pack text or file into a secure QR')
    enc.add_argument('--text', help='Text to embed into QR', default=None)
    enc.add_argument('--infile', help='File to embed into QR', default=None)
    enc.add_argument('--out', help='Output PNG filename', default='secure_qr.png')
    enc.add_argument('--key', help='Optional secret key (HMAC). If not given, uses plain SHA-256 hash', default=None)

    dec = sub.add_parser('decode', help='Decode and verify a secure QR image')
    dec.add_argument('--img', help='QR image file to decode (PNG/JPG)', required=True)
    dec.add_argument('--key', help='Secret key used to generate HMAC (if used)', default=None)

    args = parser.parse_args()

    if args.cmd == 'encode':
        cmd_encode(args)
    elif args.cmd == 'decode':
        cmd_decode(args)

if __name__ == '__main__':
    main()
