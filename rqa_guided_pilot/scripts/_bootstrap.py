"""Put rqa_pilot on sys.path."""

from __future__ import annotations

import sys
from pathlib import Path

RQA_ROOT = Path(__file__).resolve().parents[1]
SRC = RQA_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
