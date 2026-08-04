"""Resolve repository and RQA-local paths. Writes never leave rqa_guided_pilot/."""

from __future__ import annotations

from pathlib import Path

import yaml

RQA_ROOT = Path(__file__).resolve().parents[2]  # rqa_guided_pilot/
REPO_ROOT = RQA_ROOT.parent


def load_paths() -> dict:
    return yaml.safe_load((RQA_ROOT / "configs" / "paths.yaml").read_text())


def load_pilot() -> dict:
    return yaml.safe_load((RQA_ROOT / "configs" / "pilot.yaml").read_text())


def readonly_path(key: str) -> Path:
    cfg = load_paths()
    rel = cfg["readonly"][key]
    path = (REPO_ROOT / rel).resolve()
    if not str(path).startswith(str(REPO_ROOT.resolve())):
        raise RuntimeError(f"readonly path escaped repo: {path}")
    return path


def rqa_path(*parts: str) -> Path:
    path = (RQA_ROOT.joinpath(*parts)).resolve()
    if not str(path).startswith(str(RQA_ROOT.resolve())):
        raise RuntimeError(f"write path escaped rqa_guided_pilot: {path}")
    return path


def ensure_rqa_dirs() -> None:
    for sub in ("outputs", "figures", "cache", "manifests", "reports"):
        rqa_path(sub).mkdir(parents=True, exist_ok=True)
