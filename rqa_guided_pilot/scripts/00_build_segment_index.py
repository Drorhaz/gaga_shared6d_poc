#!/usr/bin/env python3
"""Build evaluation segment index from frozen window_index (read-only)."""

from __future__ import annotations

import _bootstrap  # noqa: F401
from rqa_pilot.io_readonly import build_segment_index
from rqa_pilot.paths import ensure_rqa_dirs, load_pilot, rqa_path


def main() -> None:
    ensure_rqa_dirs()
    pilot = load_pilot()
    seg = build_segment_index(pilot["exercises_eval"])
    out = rqa_path("outputs", "segment_index.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    seg.to_csv(out, index=False)
    print(f"wrote {out} n={len(seg)}")


if __name__ == "__main__":
    main()
