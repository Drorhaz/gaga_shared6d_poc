"""Unit tests for embedding, RQA, surrogates, duration."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rqa_pilot.duration import truncate_to_length
from rqa_pilot.embedding import delay_embed, n_embed
from rqa_pilot.rqa_core import auto_rqa
from rqa_pilot.surrogates import make_surrogate


def test_delay_embed_shape():
    x = np.arange(100, dtype=float)
    emb = delay_embed(x, tau=2, m=3)
    assert emb.shape == (n_embed(100, 2, 3), 3)
    assert emb[0, 0] == 0 and emb[0, 1] == 2 and emb[0, 2] == 4


def test_auto_rqa_sine_more_deterministic_than_noise():
    rng = np.random.default_rng(0)
    t = np.arange(600)
    sine = np.sin(2 * np.pi * t / 40.0)
    noise = rng.normal(size=600)
    qs = auto_rqa(sine, tau=5, m=3, mode="fixed_mean_rescaled", radius_frac=0.2)
    qn = auto_rqa(noise, tau=5, m=3, mode="fixed_mean_rescaled", radius_frac=0.2)
    assert qs["DET"] > qn["DET"]


def test_shuffle_disrupts_det():
    t = np.arange(500)
    x = np.sin(2 * np.pi * t / 25.0) + 0.1 * np.sin(2 * np.pi * t / 7.0)
    q0 = auto_rqa(x, tau=4, m=3, mode="fixed_mean_rescaled", radius_frac=0.2)
    q1 = auto_rqa(make_surrogate(x, "full_shuffle", 10, seed=1), tau=4, m=3, mode="fixed_mean_rescaled", radius_frac=0.2)
    assert q0["DET"] > q1["DET"]


def test_truncate():
    x = np.arange(50, dtype=float)
    assert truncate_to_length(x, 20).shape == (20,)


def test_target_rr_fixes_rr():
    rng = np.random.default_rng(1)
    x = rng.normal(size=400)
    q = auto_rqa(x, tau=3, m=3, mode="target_rr", target_rr=0.03)
    assert abs(q["RR"] - 0.03) < 0.015
