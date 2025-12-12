"""Utility helper functions."""
from pathlib import Path

def read_file_bytes(path: Path) -> bytes:
    with path.open('rb') as f:
        return f.read()

def ensure_parent_dir(path: Path):
    p = path.parent
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
