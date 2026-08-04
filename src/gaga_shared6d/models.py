"""Compact shared motion model and its matched convolutional baseline.

Architecture is fixed by `configs/experiment.yaml` and must not be tuned
against any longitudinal outcome. Both models consume the same tokens, the same
masks and the same targets, so the comparison between them isolates
architecture rather than task.

Input to both is 6D per link per frame: `(B, T=240, L=18, 6)`. Time is
patchified into `P = T / patch = 24` non-overlapping patches of 10 frames, so a
token is one link over one 10-frame patch.

Two self-supervised objectives are supported and are run against each other in
Stage 0:

* `masked_6d`  - reconstruct the 6D values of masked tokens.
* `masked_angular_velocity` - predict the frame-to-frame angular velocity of
  masked tokens (the MAMP-style motion target).

Only masked tokens contribute to the loss in either case.
"""

from __future__ import annotations

import math

import torch
import torch.nn as nn


# --------------------------------------------------------------------------
# structured masking
# --------------------------------------------------------------------------

def structured_mask(
    batch: int, n_links: int, n_patches: int, ratio: float,
    span_patches: tuple[int, int], generator: torch.Generator | None = None,
) -> torch.Tensor:
    """Mask whole links over contiguous temporal spans.

    Independent per-token masking is close to trivial to solve: a missing token
    can be interpolated from its immediate temporal neighbours without any
    understanding of coordination. Masking a link across a contiguous span
    forces the model to use the other links, which is the structure this
    experiment is about.

    Returns a boolean tensor `(batch, n_patches, n_links)`, True where masked.
    """
    lo, hi = span_patches
    mask = torch.zeros(batch, n_patches, n_links, dtype=torch.bool)
    target = int(round(ratio * n_patches * n_links))

    for b in range(batch):
        guard = 0
        while int(mask[b].sum()) < target and guard < 10 * n_links:
            guard += 1
            link = int(torch.randint(n_links, (1,), generator=generator))
            span = int(torch.randint(lo, hi + 1, (1,), generator=generator))
            span = min(span, n_patches)
            start = int(torch.randint(n_patches - span + 1, (1,), generator=generator))
            mask[b, start:start + span, link] = True
    return mask


# --------------------------------------------------------------------------
# compact transformer
# --------------------------------------------------------------------------

class _Attention(nn.Module):
    """Single-head attention. One head at d=32 keeps the parameter count honest."""

    def __init__(self, dim: int):
        super().__init__()
        self.qkv = nn.Linear(dim, dim * 3)
        self.proj = nn.Linear(dim, dim)
        self.scale = 1.0 / math.sqrt(dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (N, S, D)
        q, k, v = self.qkv(x).chunk(3, dim=-1)
        attn = torch.softmax((q @ k.transpose(-2, -1)) * self.scale, dim=-1)
        return self.proj(attn @ v)


class _Block(nn.Module):
    """Factorized block: attend across links, then across time, then an MLP.

    Full attention over 432 tokens would cost far more parameters and compute
    for no benefit at this data scale; factorizing keeps the model at the size
    the training set can support.
    """

    def __init__(self, dim: int, expansion: int):
        super().__init__()
        self.n1, self.spatial = nn.LayerNorm(dim), _Attention(dim)
        self.n2, self.temporal = nn.LayerNorm(dim), _Attention(dim)
        self.n3 = nn.LayerNorm(dim)
        self.mlp = nn.Sequential(
            nn.Linear(dim, dim * expansion), nn.GELU(), nn.Linear(dim * expansion, dim)
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # (B, P, L, D)
        b, p, l, d = x.shape
        h = self.n1(x).reshape(b * p, l, d)
        x = x + self.spatial(h).reshape(b, p, l, d)

        h = self.n2(x).permute(0, 2, 1, 3).reshape(b * l, p, d)
        x = x + self.temporal(h).reshape(b, l, p, d).permute(0, 2, 1, 3)

        return x + self.mlp(self.n3(x))


class SharedMotionTransformer(nn.Module):
    """Shared compact encoder over (link, time-patch) tokens."""

    def __init__(self, n_links: int = 18, n_patches: int = 24, patch_frames: int = 10,
                 dim: int = 32, n_blocks: int = 2, expansion: int = 2,
                 target_dim: int = 6):
        super().__init__()
        self.n_links, self.n_patches, self.patch_frames = n_links, n_patches, patch_frames
        self.dim, self.target_dim = dim, target_dim

        self.embed = nn.Linear(patch_frames * 6, dim)
        self.mask_token = nn.Parameter(torch.zeros(dim))
        self.link_pos = nn.Parameter(torch.zeros(n_links, dim))
        self.patch_pos = nn.Parameter(torch.zeros(n_patches, dim))
        self.blocks = nn.ModuleList([_Block(dim, expansion) for _ in range(n_blocks)])
        self.norm = nn.LayerNorm(dim)
        self.head = nn.Linear(dim, patch_frames * target_dim)

        nn.init.normal_(self.mask_token, std=0.02)
        nn.init.normal_(self.link_pos, std=0.02)
        nn.init.normal_(self.patch_pos, std=0.02)

    def patchify(self, x: torch.Tensor) -> torch.Tensor:
        """(B, T, L, 6) -> (B, P, L, patch_frames*6)"""
        b, t, l, c = x.shape
        p = t // self.patch_frames
        return (x.reshape(b, p, self.patch_frames, l, c)
                 .permute(0, 1, 3, 2, 4)
                 .reshape(b, p, l, self.patch_frames * c))

    def encode(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """Return final-layer tokens, (B, P, L, D)."""
        h = self.embed(self.patchify(x))
        if mask is not None:
            h = torch.where(mask.unsqueeze(-1), self.mask_token.expand_as(h), h)
        h = h + self.link_pos.view(1, 1, -1, self.dim) + self.patch_pos.view(1, -1, 1, self.dim)
        for blk in self.blocks:
            h = blk(h)
        return self.norm(h)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """Predictions per token, (B, P, L, patch_frames, target_dim)."""
        h = self.encode(x, mask)
        b, p, l, _ = h.shape
        return self.head(h).reshape(b, p, l, self.patch_frames, self.target_dim)

    @torch.no_grad()
    def embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Deterministic window embedding: mean pool of final tokens, (B, D).

        Fixed in FINAL_METHOD_DECISIONS.md before any result was seen. The input
        is always fully unmasked, so the embedding is a property of the window
        and not of a random mask draw.
        """
        return self.encode(x, mask=None).mean(dim=(1, 2))


# --------------------------------------------------------------------------
# matched-task convolutional baseline
# --------------------------------------------------------------------------

class ConvMaskedPredictor(nn.Module):
    """Temporal-convolution baseline on the identical task.

    Same inputs, same masks, same targets, same loss as the transformer. If a
    model of this size and shape solves the pretext task as well, the
    transformer's attention is not earning its place at this data scale.

    Per-link temporal convolutions carry the time modelling; a single linear
    mixing matrix across links carries the coordination the masking demands.
    """

    def __init__(self, n_links: int = 18, patch_frames: int = 10, channels: int = 34,
                 target_dim: int = 6, embedding_dim: int = 32):
        super().__init__()
        self.n_links = n_links
        self.patch_frames = patch_frames
        self.target_dim = target_dim
        self.channels = channels
        self.embedding_dim = embedding_dim
        self.stem = nn.Conv1d(6, channels, kernel_size=5, padding=2)
        # Cross-link mixing as a single learned L x L matrix, shared across
        # channels and time. A dense 1x1 over (links * channels) would cost
        # ~254k parameters on its own and would make this a larger model than
        # the transformer it is supposed to bound.
        self.link_mix = nn.Parameter(torch.eye(n_links) + 0.01 * torch.randn(n_links, n_links))
        self.temporal = nn.Sequential(
            nn.Conv1d(channels, channels, kernel_size=5, padding=4, dilation=2), nn.GELU(),
            nn.Conv1d(channels, channels, kernel_size=5, padding=8, dilation=4), nn.GELU(),
        )
        self.head = nn.Conv1d(channels, target_dim, kernel_size=1)
        self.mask_value = nn.Parameter(torch.zeros(6))
        self.embed_proj = nn.Linear(channels, embedding_dim)

    def _encode_features(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        """Return per-link temporal features (B, L, C, T) after stem/mix/temporal."""
        b, t, l, c = x.shape
        if mask is not None:
            frame_mask = mask.repeat_interleave(self.patch_frames, dim=1)
            x = torch.where(frame_mask.unsqueeze(-1),
                            self.mask_value.view(1, 1, 1, 6).expand_as(x), x)
        h = x.permute(0, 2, 3, 1).reshape(b * l, c, t)
        h = self.stem(h)
        ch = h.shape[1]
        h = h.reshape(b, l, ch, t)
        h = h + torch.einsum("ij,bjct->bict", self.link_mix, h)
        h = h.reshape(b * l, ch, t)
        h = h + self.temporal(h)
        return h.reshape(b, l, ch, t)

    def forward(self, x: torch.Tensor, mask: torch.Tensor | None = None) -> torch.Tensor:
        b, t, l, _ = x.shape
        h = self._encode_features(x, mask)
        out = self.head(h.reshape(b * l, self.channels, t))
        out = out.reshape(b, l, self.target_dim, t).permute(0, 3, 1, 2)
        p = t // self.patch_frames
        return (out.reshape(b, p, self.patch_frames, l, self.target_dim)
                   .permute(0, 1, 3, 2, 4))

    @torch.no_grad()
    def embedding(self, x: torch.Tensor) -> torch.Tensor:
        """Deterministic 32D window embedding: mean pool of encoder features.

        Fully unmasked, matching the Transformer's embedding contract so that
        downstream aggregation is identical across architectures.
        """
        h = self._encode_features(x, mask=None)  # (B, L, C, T)
        pooled = h.mean(dim=(1, 3))              # (B, C)
        return self.embed_proj(pooled)


# --------------------------------------------------------------------------

def masked_loss(pred: torch.Tensor, target: torch.Tensor, mask: torch.Tensor) -> torch.Tensor:
    """Mean squared error over masked tokens only.

    `pred`/`target` are (B, P, L, patch_frames, C); `mask` is (B, P, L).
    """
    m = mask.unsqueeze(-1).unsqueeze(-1).expand_as(target)
    if not m.any():
        return pred.sum() * 0.0
    return ((pred - target) ** 2)[m].mean()


def count_parameters(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)
