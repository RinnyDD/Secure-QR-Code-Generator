from __future__ import annotations

import sys
from pathlib import Path

# Ensure tests can import modules from ./src
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
