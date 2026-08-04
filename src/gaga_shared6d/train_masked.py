"""Training loops for masked predictors (S5 conv, S6 transformer)."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import numpy as np
import torch
from torch.utils.data import DataLoader, TensorDataset

from . import models, trivial


@dataclass
class TrainResult:
    best_state: dict
    history: list[dict] = field(default_factory=list)
    best_epoch: int = 0
    best_val_loss: float = float("inf")
    n_params: int = 0
    seconds: float = 0.0
    target_dim: int = 6
    architecture: str = "conv"


def _make_loaders(
    x_train_6d: np.ndarray,
    x_val_6d: np.ndarray,
    y_train: np.ndarray | None,
    y_val: np.ndarray | None,
    objective: str,
    batch_size: int,
) -> tuple[DataLoader, DataLoader]:
    def _loader(x6, y, shuffle):
        xt = torch.from_numpy(x6)
        if objective == "masked_6d":
            ds = TensorDataset(xt, xt)
        else:
            ds = TensorDataset(xt, torch.from_numpy(y))
        return DataLoader(ds, batch_size=batch_size, shuffle=shuffle)

    return _loader(x_train_6d, y_train, True), _loader(x_val_6d, y_val, False)


def _train_loop(
    net: torch.nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    *,
    objective: str,
    mask_ratio: float,
    span_patches: tuple[int, int],
    seed: int,
    max_epochs: int,
    lr: float,
    weight_decay: float,
    patience: int,
    patch_frames: int,
    architecture: str,
) -> TrainResult:
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=weight_decay)
    best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}
    best_val, best_epoch, stall = float("inf"), 0, 0
    history = []
    t0 = time.time()
    g_train = torch.Generator().manual_seed(seed)
    target_dim = 6 if objective == "masked_6d" else 3

    for epoch in range(max_epochs):
        net.train()
        tr_loss, n = 0.0, 0
        for xb, yb in train_loader:
            b, t, l, _ = xb.shape
            p = t // patch_frames
            mask = models.structured_mask(b, l, p, mask_ratio, span_patches, g_train)
            target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
            pred = net(xb, mask)
            loss = models.masked_loss(pred, target, mask)
            opt.zero_grad()
            loss.backward()
            opt.step()
            tr_loss += float(loss.detach()) * b
            n += b
        tr_loss /= max(n, 1)

        net.eval()
        va_loss, vn = 0.0, 0
        triv_m, triv_i = 0.0, 0.0
        g_val = torch.Generator().manual_seed(seed + 17_001 + epoch)
        with torch.no_grad():
            for xb, yb in val_loader:
                b, t, l, _ = xb.shape
                p = t // patch_frames
                mask = models.structured_mask(b, l, p, mask_ratio, span_patches, g_val)
                target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
                pred = net(xb, mask)
                loss = models.masked_loss(pred, target, mask)
                te = trivial.trivial_errors(target, mask)
                va_loss += float(loss) * b
                triv_m += te["mean_motion"] * b
                triv_i += te["interpolation"] * b
                vn += b
        va_loss /= max(vn, 1)
        triv_m /= max(vn, 1)
        triv_i /= max(vn, 1)
        triv_best = min(triv_m, triv_i)
        sk = trivial.skill(va_loss, triv_best)
        history.append({
            "epoch": epoch, "train_loss": tr_loss, "val_loss": va_loss,
            "trivial_best": triv_best, "skill": sk,
        })
        if va_loss < best_val - 1e-6:
            best_val, best_epoch, stall = va_loss, epoch, 0
            best_state = {k: v.detach().cpu().clone() for k, v in net.state_dict().items()}
        else:
            stall += 1
            if stall >= patience:
                break

    return TrainResult(
        best_state=best_state, history=history, best_epoch=best_epoch,
        best_val_loss=best_val, n_params=models.count_parameters(net),
        seconds=time.time() - t0, target_dim=target_dim,
        architecture=architecture,
    )


def train_conv(
    x_train_6d: np.ndarray,
    x_val_6d: np.ndarray,
    y_train: np.ndarray | None,
    y_val: np.ndarray | None,
    objective: str,
    mask_ratio: float,
    span_patches: tuple[int, int],
    seed: int,
    channels: int = 34,
    batch_size: int = 16,
    max_epochs: int = 60,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    patience: int = 8,
    n_links: int = 18,
    patch_frames: int = 10,
    embedding_dim: int = 32,
) -> TrainResult:
    """Train ConvMaskedPredictor (S5)."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    target_dim = 6 if objective == "masked_6d" else 3
    net = models.ConvMaskedPredictor(
        n_links=n_links, patch_frames=patch_frames, channels=channels,
        target_dim=target_dim, embedding_dim=embedding_dim,
    )
    train_loader, val_loader = _make_loaders(
        x_train_6d, x_val_6d, y_train, y_val, objective, batch_size,
    )
    return _train_loop(
        net, train_loader, val_loader,
        objective=objective, mask_ratio=mask_ratio, span_patches=span_patches,
        seed=seed, max_epochs=max_epochs, lr=lr,
        weight_decay=weight_decay, patience=patience, patch_frames=patch_frames,
        architecture="conv",
    )


def train_transformer(
    x_train_6d: np.ndarray,
    x_val_6d: np.ndarray,
    y_train: np.ndarray | None,
    y_val: np.ndarray | None,
    objective: str,
    mask_ratio: float,
    span_patches: tuple[int, int],
    seed: int,
    batch_size: int = 16,
    max_epochs: int = 60,
    lr: float = 1e-3,
    weight_decay: float = 1e-4,
    patience: int = 8,
    n_links: int = 18,
    n_patches: int = 24,
    patch_frames: int = 10,
    hidden_dim: int = 32,
    n_blocks: int = 2,
    ffn_expansion: int = 2,
) -> TrainResult:
    """Train SharedMotionTransformer (S6) with the same loop as the conv baseline."""
    torch.manual_seed(seed)
    np.random.seed(seed)
    target_dim = 6 if objective == "masked_6d" else 3
    net = models.SharedMotionTransformer(
        n_links=n_links, n_patches=n_patches, patch_frames=patch_frames,
        dim=hidden_dim, n_blocks=n_blocks, expansion=ffn_expansion,
        target_dim=target_dim,
    )
    train_loader, val_loader = _make_loaders(
        x_train_6d, x_val_6d, y_train, y_val, objective, batch_size,
    )
    return _train_loop(
        net, train_loader, val_loader,
        objective=objective, mask_ratio=mask_ratio, span_patches=span_patches,
        seed=seed, max_epochs=max_epochs, lr=lr,
        weight_decay=weight_decay, patience=patience, patch_frames=patch_frames,
        architecture="transformer",
    )


@torch.no_grad()
def score_arrays(
    net: torch.nn.Module,
    x6: np.ndarray,
    y: np.ndarray | None,
    objective: str,
    mask_ratio: float,
    span: tuple[int, int],
    patch_frames: int,
    seed: int,
    trivial_which: str = "both",
    batch_size: int = 32,
) -> dict:
    """Score a split with a fixed mask-generator seed.

    Primary analyses use ``trivial_which='both'`` (best of mean-motion and
    interpolation). Mean-motion-only is retained for fast sanity controls.
    """
    if len(x6) == 0:
        return {
            "error": float("nan"), "trivial_mean": float("nan"),
            "trivial_interp": float("nan"), "trivial_best": float("nan"),
            "skill": float("nan"), "n": 0,
        }
    if objective == "masked_6d":
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(x6))
    else:
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(y))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)
    net.eval()
    total, tm, ti, n = 0.0, 0.0, 0.0, 0
    g = torch.Generator().manual_seed(seed)
    with torch.no_grad():
        for xb, yb in loader:
            b, t, l, _ = xb.shape
            p = t // patch_frames
            mask = models.structured_mask(b, l, p, mask_ratio, span, g)
            target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
            pred = net(xb, mask)
            loss = models.masked_loss(pred, target, mask)
            te = trivial.trivial_errors(target, mask, which=trivial_which)
            total += float(loss) * b
            tm += te.get("mean_motion", 0.0) * b
            ti += te.get("interpolation", 0.0) * b
            n += b
    err = total / max(n, 1)
    tm = tm / max(n, 1) if trivial_which in ("both", "mean_motion") else float("nan")
    ti = ti / max(n, 1) if trivial_which in ("both", "interpolation") else float("nan")
    if trivial_which == "both":
        triv_best = min(tm, ti)
    elif trivial_which == "mean_motion":
        triv_best = tm
    else:
        triv_best = ti
    return {
        "error": err, "trivial_mean": tm, "trivial_interp": ti,
        "trivial_best": triv_best, "skill": trivial.skill(err, triv_best), "n": n,
    }


@torch.no_grad()
def per_link_masked_error(
    net: torch.nn.Module,
    x6: np.ndarray,
    y: np.ndarray | None,
    objective: str,
    mask_ratio: float,
    span: tuple[int, int],
    patch_frames: int,
    seed: int,
    n_links: int = 18,
    batch_size: int = 32,
) -> np.ndarray:
    """Mean masked MSE per link on a split. Shape (n_links,)."""
    if objective == "masked_6d":
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(x6))
    else:
        ds = TensorDataset(torch.from_numpy(x6), torch.from_numpy(y))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False)
    sums = np.zeros(n_links, dtype=np.float64)
    counts = np.zeros(n_links, dtype=np.float64)
    g = torch.Generator().manual_seed(seed)
    net.eval()
    with torch.no_grad():
        for xb, yb in loader:
            b, t, l, _ = xb.shape
            p = t // patch_frames
            mask = models.structured_mask(b, l, p, mask_ratio, span, g)
            target = yb.reshape(b, p, patch_frames, l, yb.shape[-1]).permute(0, 1, 3, 2, 4)
            pred = net(xb, mask)
            se = ((pred - target) ** 2).mean(dim=(-1, -2))  # (B, P, L)
            for li in range(l):
                m = mask[:, :, li]
                if m.any():
                    sums[li] += float(se[:, :, li][m].sum().item())
                    counts[li] += float(m.sum().item())
    out = np.full(n_links, np.nan)
    ok = counts > 0
    out[ok] = sums[ok] / counts[ok]
    return out


@torch.no_grad()
def embed_windows(net: torch.nn.Module, x_6d: np.ndarray, batch_size: int = 32) -> np.ndarray:
    net.eval()
    outs = []
    for i in range(0, len(x_6d), batch_size):
        xb = torch.from_numpy(x_6d[i:i + batch_size])
        outs.append(net.embedding(xb).cpu().numpy())
    return np.concatenate(outs, axis=0) if outs else np.zeros((0, 32), dtype=np.float32)
