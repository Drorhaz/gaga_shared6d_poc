"""Matched trivial baselines for dimensionless skill.

skill(T) = [error_trivial(T) - error_model(T)] / error_trivial(T)

Trivial baselines operate on the same masked tokens and the same target tensor
as the model, so skill is dimensionless and comparable across objectives.
"""

from __future__ import annotations

import numpy as np
import torch


def mean_motion_predict(
    target: torch.Tensor, mask: torch.Tensor,
) -> torch.Tensor:
    """Predict the mean of unmasked tokens (broadcast to masked positions)."""
    inv = ~mask
    b, p, l, f, c = target.shape
    flat = target.reshape(b, p * l, f * c)
    inv_flat = inv.reshape(b, p * l)
    pred = torch.zeros_like(target)
    for i in range(b):
        if inv_flat[i].any():
            m = flat[i][inv_flat[i]].mean(dim=0)  # (F*C,)
        else:
            m = flat[i].mean(dim=0)
        pred[i] = m.view(1, 1, f, c).expand(p, l, f, c)
    return pred


def interpolation_predict(
    target: torch.Tensor, mask: torch.Tensor,
) -> torch.Tensor:
    """Linear interpolate along time within each link from unmasked patches."""
    b, p, l, f, c = target.shape
    series = target.mean(dim=3).detach().cpu().numpy()  # (B, P, L, C)
    msk = mask.detach().cpu().numpy()
    pred_series = series.copy()
    x_all = np.arange(p, dtype=np.float64)
    for bi in range(b):
        for li in range(l):
            known = ~msk[bi, :, li]
            if known.all() or not known.any():
                continue
            xp = x_all[known]
            fp = series[bi, known, li, :]  # (K, C)
            for ci in range(c):
                pred_series[bi, :, li, ci] = np.interp(x_all, xp, fp[:, ci])
    out = torch.from_numpy(pred_series.astype(np.float32)).to(target.device)
    return out.unsqueeze(3).expand(b, p, l, f, c)


def masked_mse(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> float:
    m = mask.unsqueeze(-1).unsqueeze(-1).expand_as(target)
    if not m.any():
        return float("nan")
    return float(((pred - target) ** 2)[m].mean().item())


@torch.no_grad()
def trivial_errors(
    target: torch.Tensor, mask: torch.Tensor, which: str = "both",
) -> dict[str, float]:
    out: dict[str, float] = {}
    if which in ("both", "mean_motion"):
        out["mean_motion"] = masked_mse(mean_motion_predict(target, mask), target, mask)
    if which in ("both", "interpolation"):
        out["interpolation"] = masked_mse(interpolation_predict(target, mask), target, mask)
    return out


def skill(error_model: float, error_trivial: float) -> float:
    if not (error_trivial > 0) or error_trivial != error_trivial:
        return float("nan")
    return (error_trivial - error_model) / error_trivial
