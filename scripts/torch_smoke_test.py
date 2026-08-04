#!/usr/bin/env python3
"""CPU smoke test for the S6 model stack, run before any real training.

Deliberately small and fast. It checks that the pieces fit together, that the
capacity limits hold, that masking behaves, and that runs are reproducible.
It does NOT train on real data and produces no scientific result.

Real windows are used for one shape check only, if they exist, so that the
tensor layout is confirmed against the actual S4 output rather than against
synthetic data alone.

Usage:
    ./.venv/bin/python scripts/torch_smoke_test.py
"""

from __future__ import annotations

import platform
import sys
import time
from pathlib import Path

import numpy as np
import torch
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gaga_shared6d import models, provenance, rotations  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
AXES = ("rx", "ry", "rz")

# Capacity limits from the plan. The transformer must stay compact and the
# baseline must stay clearly smaller, or the comparison is not matched.
TRANSFORMER_MAX_PARAMS = 45_000
CONV_MAX_PARAMS = 20_000

results: list[dict] = []


def check(name: str, ok: bool, detail: str = "") -> bool:
    results.append({"check": name, "passed": bool(ok), "detail": detail})
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    if detail:
        print(f"         {detail}")
    return ok


def main() -> int:
    torch.set_num_threads(4)
    cfg = yaml.safe_load((ROOT / "configs/experiment.yaml").read_text())
    mcfg = cfg["model"]

    print("=" * 74)
    print("TORCH SMOKE TEST (CPU)")
    print("=" * 74)
    print(f"python {sys.version.split()[0]} | torch {torch.__version__} | "
          f"numpy {np.__version__}")
    print(f"{platform.platform()} | {platform.machine()} | "
          f"threads {torch.get_num_threads()}")
    print(f"cuda {torch.cuda.is_available()} | mps {torch.backends.mps.is_available()} "
          f"(available but unused: CPU float32 is deterministic, MPS is not)")

    n_links, n_patches = mcfg["n_links"], mcfg["n_patches"]
    patch = mcfg["patch_frames"]
    frames = n_patches * patch
    batch = 4

    print("\n-- environment --")
    check("torch imports and runs on CPU", torch.device("cpu").type == "cpu",
          f"torch {torch.__version__}")
    check("numpy interop works with numpy 2.5",
          float(torch.from_numpy(np.ones(3)).sum()) == 3.0,
          "numpy -> torch -> numpy round trip")

    print("\n-- model construction and capacity --")
    torch.manual_seed(0)
    model = models.SharedMotionTransformer(
        n_links=n_links, n_patches=n_patches, patch_frames=patch,
        dim=mcfg["hidden_dim"], n_blocks=mcfg["n_blocks"],
        expansion=mcfg["ffn_expansion"], target_dim=6)
    n_par = models.count_parameters(model)
    check(f"transformer stays under {TRANSFORMER_MAX_PARAMS:,} parameters",
          n_par <= TRANSFORMER_MAX_PARAMS,
          f"{n_par:,} parameters (d={mcfg['hidden_dim']}, "
          f"{mcfg['n_blocks']} blocks, {n_links}x{n_patches} tokens)")

    conv = models.ConvMaskedPredictor(n_links=n_links, patch_frames=patch, target_dim=6)
    n_conv = models.count_parameters(conv)
    check(f"conv baseline stays under {CONV_MAX_PARAMS:,} parameters",
          n_conv <= CONV_MAX_PARAMS and n_conv < n_par,
          f"{n_conv:,} parameters, {n_conv/n_par:.0%} of the transformer")

    print("\n-- structured masking --")
    g = torch.Generator().manual_seed(0)
    span = [s // patch for s in mcfg["mask_span_frames"]]
    for ratio in mcfg["mask_ratio_sweep"]:
        m = models.structured_mask(batch, n_links, n_patches, ratio, tuple(span), g)
        got = float(m.float().mean())
        check(f"mask ratio {ratio:.0%} achieved",
              abs(got - ratio) < 0.08,
              f"requested {ratio:.0%}, achieved {got:.1%}")

    # Structure is measured as run length: the number of maximal contiguous
    # masked runs per link, not the envelope from first to last masked patch.
    # At a 50 percent ratio each link is drawn several times, so adjacent draws
    # legitimately merge into longer runs; what must not happen is scattering
    # into isolated single patches, which is what independent per-token masking
    # would produce and what the model could solve by interpolation alone.
    def run_lengths(mask_bpl: torch.Tensor) -> list[int]:
        lengths = []
        for bi in range(mask_bpl.shape[0]):
            for li in range(mask_bpl.shape[2]):
                col = mask_bpl[bi, :, li].tolist()
                run = 0
                for v in col + [False]:
                    if v:
                        run += 1
                    elif run:
                        lengths.append(run)
                        run = 0
        return lengths

    m = models.structured_mask(batch, n_links, n_patches, 0.5, tuple(span), g)
    runs = run_lengths(m)
    singles = sum(1 for r in runs if r < span[0])
    independent = torch.rand(batch, n_patches, n_links, generator=g) < 0.5
    ind_runs = run_lengths(independent)
    med, ind_med = float(np.median(runs)), float(np.median(ind_runs))
    check("masks are contiguous spans, not scattered patches",
          singles == 0 and med >= span[0] and med > 2 * ind_med,
          f"{len(runs)} runs, median length {med:.0f} patches, "
          f"{singles} shorter than the configured minimum of {span[0]}; "
          f"independent per-token masking at the same ratio would give "
          f"median {ind_med:.0f}")

    print("\n-- forward and backward on both objectives --")
    x = torch.randn(batch, frames, n_links, 6)
    mask = models.structured_mask(batch, n_links, n_patches, 0.5, tuple(span), g)

    for objective, target_dim in (("masked_6d", 6), ("masked_angular_velocity", 3)):
        torch.manual_seed(0)
        net = models.SharedMotionTransformer(
            n_links=n_links, n_patches=n_patches, patch_frames=patch,
            dim=mcfg["hidden_dim"], n_blocks=mcfg["n_blocks"],
            expansion=mcfg["ffn_expansion"], target_dim=target_dim)
        pred = net(x, mask)
        tgt = torch.randn_like(pred)
        loss = models.masked_loss(pred, tgt, mask)
        loss.backward()
        grads = sum(1 for p in net.parameters() if p.grad is not None and p.grad.abs().sum() > 0)
        total = sum(1 for _ in net.parameters())
        check(f"{objective}: forward, loss and backward",
              tuple(pred.shape) == (batch, n_patches, n_links, patch, target_dim)
              and torch.isfinite(loss) and grads == total,
              f"pred {tuple(pred.shape)}, loss {float(loss.detach()):.4f}, "
              f"{grads}/{total} tensors received gradient")

    pred_c = conv(x, mask)
    check("conv baseline matches the transformer's output contract",
          tuple(pred_c.shape) == (batch, n_patches, n_links, patch, 6),
          f"pred {tuple(pred_c.shape)}")

    print("\n-- loss only counts masked tokens --")
    torch.manual_seed(0)
    net = models.SharedMotionTransformer(
        n_links=n_links, n_patches=n_patches, patch_frames=patch,
        dim=mcfg["hidden_dim"], n_blocks=mcfg["n_blocks"], expansion=mcfg["ffn_expansion"])
    pred = net(x, mask)
    tgt = net.patchify(x).reshape(batch, n_patches, n_links, patch, 6)
    perturbed = tgt.clone()
    perturbed[~mask] += 100.0  # change only UNmasked tokens
    same = torch.allclose(models.masked_loss(pred, tgt, mask),
                          models.masked_loss(pred, perturbed, mask))
    check("unmasked tokens do not contribute to the loss", same,
          "perturbing every unmasked target by +100 leaves the loss unchanged")

    print("\n-- determinism --")
    def one_run(seed: int) -> float:
        torch.manual_seed(seed)
        n = models.SharedMotionTransformer(
            n_links=n_links, n_patches=n_patches, patch_frames=patch,
            dim=mcfg["hidden_dim"], n_blocks=mcfg["n_blocks"],
            expansion=mcfg["ffn_expansion"])
        opt = torch.optim.AdamW(n.parameters(), lr=1e-3)
        gg = torch.Generator().manual_seed(seed)
        xx = torch.randn(batch, frames, n_links, 6, generator=gg)
        mm = models.structured_mask(batch, n_links, n_patches, 0.5, tuple(span), gg)
        tt = n.patchify(xx).reshape(batch, n_patches, n_links, patch, 6)
        last = float("nan")
        for _ in range(5):
            opt.zero_grad()
            loss = models.masked_loss(n(xx, mm), tt, mm)
            loss.backward()
            opt.step()
            last = float(loss.detach())
        return last

    a, b = one_run(0), one_run(0)
    check("identical seed gives identical loss", a == b, f"{a:.10f} vs {b:.10f}")
    c = one_run(1)
    check("different seed gives a different trajectory", a != c,
          f"seed 0 {a:.6f}, seed 1 {c:.6f}")

    print("\n-- the pretext task is learnable at this size --")
    torch.manual_seed(0)
    net = models.SharedMotionTransformer(
        n_links=n_links, n_patches=n_patches, patch_frames=patch,
        dim=mcfg["hidden_dim"], n_blocks=mcfg["n_blocks"], expansion=mcfg["ffn_expansion"])
    opt = torch.optim.AdamW(net.parameters(), lr=3e-3)
    gg = torch.Generator().manual_seed(7)
    # Smooth structured signal, not white noise: white noise is unpredictable by
    # construction and would tell us nothing.
    t_axis = torch.linspace(0, 4 * np.pi, frames).view(1, frames, 1, 1)
    phase = torch.rand(batch, 1, n_links, 6, generator=gg) * 2 * np.pi
    xx = torch.sin(t_axis + phase)
    tt = net.patchify(xx).reshape(batch, n_patches, n_links, patch, 6)
    mm = models.structured_mask(batch, n_links, n_patches, 0.5, tuple(span), gg)
    first, last, t0 = None, None, time.time()
    for step in range(60):
        opt.zero_grad()
        loss = models.masked_loss(net(xx, mm), tt, mm)
        loss.backward()
        opt.step()
        if step == 0:
            first = float(loss.detach())
        last = float(loss.detach())
    dt = time.time() - t0
    check("loss decreases on a smooth synthetic signal",
          last < first * 0.5,
          f"{first:.4f} -> {last:.4f} over 60 steps in {dt:.1f}s "
          f"({dt/60*1000:.0f} ms/step at batch {batch})")

    print("\n-- deterministic embedding extraction --")
    emb1 = net.embedding(xx)
    emb2 = net.embedding(xx)
    check("embedding is 32-D, one vector per window",
          tuple(emb1.shape) == (batch, mcfg["embedding_dim"]),
          f"{tuple(emb1.shape)} from mean pooling {n_patches*n_links} final tokens")
    check("embedding is deterministic and mask-free",
          torch.equal(emb1, emb2),
          "two extractions on the same input are bit-identical")

    print("\n-- shape check against real S4 windows --")
    idx_path = ROOT / "outputs/s4_windows/window_index.csv"
    rot_dir = ROOT / "data/immutable/rotvec_18link"
    if idx_path.exists():
        import pandas as pd

        widx = pd.read_csv(idx_path)
        linkcfg = yaml.safe_load((ROOT / "configs/canonical_links_18.yaml").read_text())
        link_ids = [l["id"] for l in linkcfg["links"]]
        row = widx.iloc[0]
        df = pd.read_parquet(rot_dir / f"{row.recording_id}.parquet")
        rv = df[[f"{l}_{a}" for l in link_ids for a in AXES]].to_numpy()
        rv = rv[int(row.start_frame):int(row.end_frame)].reshape(-1, n_links, 3)
        mats = rotations.rotvec_to_matrix(rv.reshape(-1, 3))
        sixd = rotations.matrix_to_6d(mats).reshape(1, frames, n_links, 6)
        xr = torch.from_numpy(sixd).float()
        out = net(xr, models.structured_mask(1, n_links, n_patches, 0.5, tuple(span), g))
        emb = net.embedding(xr)
        check("a real 2 s window flows through the model",
              tuple(xr.shape) == (1, frames, n_links, 6)
              and tuple(out.shape) == (1, n_patches, n_links, patch, 6)
              and tuple(emb.shape) == (1, mcfg["embedding_dim"])
              and bool(torch.isfinite(emb).all()),
              f"{row.window_id} from {row.recording_id}: input {tuple(xr.shape)} "
              f"-> tokens -> embedding {tuple(emb.shape)}")
    else:
        check("real-window shape check skipped", True, "S4 window index not present")

    n_pass = sum(r["passed"] for r in results)
    print("\n" + "=" * 74)
    print(f"{n_pass}/{len(results)} checks passed")
    print("=" * 74)

    provenance.write_json(
        ROOT / "outputs/smoke_test/torch_smoke_test.json",
        {
            **provenance.run_stamp("torch_smoke_test"),
            "torch": torch.__version__,
            "numpy": np.__version__,
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "machine": platform.machine(),
            "cuda_available": torch.cuda.is_available(),
            "mps_available": bool(torch.backends.mps.is_available()),
            "device_used": "cpu",
            "transformer_parameters": n_par,
            "conv_baseline_parameters": n_conv,
            "checks": results,
            "all_passed": n_pass == len(results),
        },
    )
    return 0 if n_pass == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
