"""Endpoint-relative rotation extraction and the 6D representation.

Rotation math is byte-faithful to the validated Layer 2 pipeline in
``gaga_jcvpca/src/gaga_jcvpca/rotations.py``:

    q_rel = inv(q_parent) * q_child     (SciPy composition, [x, y, z, w])
    -> sign-continuity correction along time
    -> SO(3) log map to rotation vectors
    -> zero-phase Butterworth low-pass in the tangent space

The one deliberate departure: the parent/child pair is an *endpoint* pair
drawn from the canonical 18-link set rather than an adjacent pair from each
participant's native hierarchy. Because a parent-relative chain telescopes,

    R_Ab->Spine2 · R_Spine2->Spine3 · R_Spine3->Spine4 · R_Spine4->Chest
        = R_Ab->Chest = inv(R_Ab_global) · R_Chest_global

the endpoint-relative rotation IS the composed chain, so 252/790 gain
`Ab_to_Chest` and `Neck_to_Head` without any chain product being computed.
``verify_chain_composition`` checks that identity numerically.

Extraction always precedes filtering: filtering sub-links and then combining
is not equal to combining and then filtering.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt
from scipy.spatial.transform import Rotation

PI = float(np.pi)


# --- relative rotation ---------------------------------------------------

def relative_quaternions(parent_quats: np.ndarray, child_quats: np.ndarray) -> np.ndarray:
    """q_rel = inv(q_parent) * q_child for aligned (n, 4) SciPy-order arrays."""
    parent_quats = np.asarray(parent_quats, dtype=float)
    child_quats = np.asarray(child_quats, dtype=float)
    if parent_quats.shape != child_quats.shape or parent_quats.ndim != 2:
        raise ValueError("parent_quats and child_quats must both have shape (n, 4)")
    return (Rotation.from_quat(parent_quats).inv() * Rotation.from_quat(child_quats)).as_quat()


def apply_sign_continuity(quats: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Remove quaternion double-cover sign flips along time.

    Vectorised equivalent of the source project's sequential loop: a frame is
    negated when the running parity of adjacent-frame sign disagreements is odd.
    """
    quats = np.asarray(quats, dtype=float)
    if quats.ndim != 2 or quats.shape[1] != 4:
        raise ValueError("quats must have shape (n, 4)")
    if len(quats) < 2:
        return quats.copy(), np.zeros(len(quats), dtype=bool)
    disagree = np.sum(quats[1:] * quats[:-1], axis=1) < 0.0
    parity = np.concatenate([[False], np.cumsum(disagree) % 2 == 1])
    corrected = np.where(parity[:, None], -quats, quats)
    return corrected, parity


def quats_to_rotvec(quats: np.ndarray) -> np.ndarray:
    return Rotation.from_quat(np.asarray(quats, dtype=float).copy()).as_rotvec()


# --- filtering -----------------------------------------------------------

def design_butterworth_sos(cutoff_hz: float, sampling_rate_hz: float, order: int) -> np.ndarray:
    return np.asarray(
        butter(order, cutoff_hz / (sampling_rate_hz / 2.0), btype="low", output="sos"),
        dtype=float,
    )


def _min_filtfilt_length(sos: np.ndarray) -> int:
    ntaps = 2 * sos.shape[0] + 1
    ntaps -= min((sos[:, 2] == 0).sum(), (sos[:, 5] == 0).sum())
    return 3 * int(ntaps) + 1


def filter_rotvec(components: np.ndarray, sos: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Zero-phase Butterworth on rx/ry/rz over contiguous finite segments.

    Segments shorter than sosfiltfilt's padding requirement are left NaN rather
    than crashing, matching the source pipeline's behaviour.
    """
    components = np.asarray(components, dtype=float)
    if components.ndim != 2 or components.shape[1] != 3:
        raise ValueError("components must have shape (n_frames, 3)")
    finite = np.all(np.isfinite(components), axis=1)
    out = np.full_like(components, np.nan)
    applied = np.zeros(len(components), dtype=bool)
    min_len = _min_filtfilt_length(sos)

    start = None
    for idx in range(len(finite) + 1):
        val = finite[idx] if idx < len(finite) else False
        if val and start is None:
            start = idx
        elif not val and start is not None:
            seg = components[start:idx]
            if seg.shape[0] >= min_len:
                for axis in range(3):
                    out[start:idx, axis] = sosfiltfilt(sos, seg[:, axis])
                applied[start:idx] = True
            start = None
    return out, applied


def extract_link_rotvec(
    parent_quats: np.ndarray,
    child_quats: np.ndarray,
    sos: np.ndarray | None,
    near_pi_fraction: float = 0.95,
    jump_fail_rad: float = 1.0,
) -> dict:
    """Full per-link pipeline. Returns raw and filtered rotvecs plus QC flags."""
    n = len(parent_quats)
    norms_p = np.linalg.norm(parent_quats, axis=1)
    norms_c = np.linalg.norm(child_quats, axis=1)
    invalid = (
        ~np.isfinite(norms_p) | ~np.isfinite(norms_c) | (norms_p < 1e-6) | (norms_c < 1e-6)
    )

    identity = np.array([0.0, 0.0, 0.0, 1.0])
    safe_p = np.where(invalid[:, None], identity, np.nan_to_num(parent_quats, nan=0.0))
    safe_c = np.where(invalid[:, None], identity, np.nan_to_num(child_quats, nan=0.0))

    rel = relative_quaternions(safe_p, safe_c)
    rel, _ = apply_sign_continuity(rel)
    rotvec = quats_to_rotvec(rel)
    rotvec[invalid] = np.nan

    angle = np.linalg.norm(rotvec, axis=1)
    jumps = np.full(n, False)
    if n > 1:
        step = np.linalg.norm(np.diff(rotvec, axis=0), axis=1)
        jumps[1:] = step > jump_fail_rad

    filtered, applied = (
        filter_rotvec(rotvec, sos) if sos is not None else (rotvec.copy(), np.isfinite(angle))
    )

    return {
        "rotvec_raw": rotvec,
        "rotvec": filtered,
        "angle_rad": angle,
        "quaternion_invalid": invalid,
        "near_pi": np.isfinite(angle) & (angle > near_pi_fraction * PI),
        "rotation_jump": jumps,
        "filter_applied": applied,
    }


def verify_chain_composition(
    global_quats: np.ndarray, chain_indices: list[int], tol: float = 1e-9
) -> dict:
    """Check that the endpoint-relative rotation equals the composed chain.

    ``chain_indices`` lists bone indices from parent endpoint through every
    intermediate bone to the child endpoint. Returns the maximum geodesic
    discrepancy in radians and degrees.
    """
    if len(chain_indices) < 2:
        raise ValueError("chain_indices needs at least a parent and a child")

    endpoint = relative_quaternions(
        global_quats[:, chain_indices[0], :], global_quats[:, chain_indices[-1], :]
    )

    composed = Rotation.from_quat(
        relative_quaternions(
            global_quats[:, chain_indices[0], :], global_quats[:, chain_indices[1], :]
        )
    )
    for a, b in zip(chain_indices[1:-1], chain_indices[2:]):
        composed = composed * Rotation.from_quat(
            relative_quaternions(global_quats[:, a, :], global_quats[:, b, :])
        )

    delta = Rotation.from_quat(endpoint).inv() * composed
    err = np.linalg.norm(delta.as_rotvec(), axis=1)
    err = np.minimum(err, 2 * PI - err)  # geodesic distance on SO(3)
    finite = err[np.isfinite(err)]
    max_err = float(finite.max()) if finite.size else float("nan")
    return {
        "max_error_rad": max_err,
        "max_error_deg": float(np.degrees(max_err)),
        "mean_error_rad": float(finite.mean()) if finite.size else float("nan"),
        "n_frames": int(len(err)),
        "passed": bool(finite.size and max_err <= tol),
    }


# --- direct (unfiltered) path: quat -> matrix, no rotvec -------------------

def quats_to_matrix(quats: np.ndarray) -> np.ndarray:
    """Quaternion array (n, 4) -> rotation matrices (n, 3, 3)."""
    quats = np.asarray(quats, dtype=float)
    out = np.full((len(quats), 3, 3), np.nan)
    ok = np.all(np.isfinite(quats), axis=1) & (np.linalg.norm(quats, axis=1) > 1e-6)
    if ok.any():
        out[ok] = Rotation.from_quat(quats[ok]).as_matrix()
    return out


def extract_link_matrix_direct(
    parent_quats: np.ndarray, child_quats: np.ndarray,
) -> dict:
    """Direct sensitivity path: no rotvec, no Butterworth.

    ```text
    global parent/child quaternions
    → parent-relative quaternion
    → sign continuity
    → rotation matrix
    → (caller converts to 6D)
    ```

    This is a sensitivity branch only. The validated primary path still filters
    in rotation-vector tangent space before forming the matrix.
    """
    n = len(parent_quats)
    norms_p = np.linalg.norm(parent_quats, axis=1)
    norms_c = np.linalg.norm(child_quats, axis=1)
    invalid = (
        ~np.isfinite(norms_p) | ~np.isfinite(norms_c) | (norms_p < 1e-6) | (norms_c < 1e-6)
    )
    identity = np.array([0.0, 0.0, 0.0, 1.0])
    safe_p = np.where(invalid[:, None], identity, np.nan_to_num(parent_quats, nan=0.0))
    safe_c = np.where(invalid[:, None], identity, np.nan_to_num(child_quats, nan=0.0))

    rel, _ = apply_sign_continuity(relative_quaternions(safe_p, safe_c))
    mats = quats_to_matrix(rel)
    mats[invalid] = np.nan
    return {"matrix": mats, "quaternion_invalid": invalid, "rel_quaternion": rel}


# --- 6D representation (Zhou et al. 2019) --------------------------------

def rotvec_to_matrix(rotvec: np.ndarray) -> np.ndarray:
    out = np.full((len(rotvec), 3, 3), np.nan)
    ok = np.all(np.isfinite(rotvec), axis=1)
    if ok.any():
        out[ok] = Rotation.from_rotvec(rotvec[ok]).as_matrix()
    return out


def matrix_to_6d(mats: np.ndarray) -> np.ndarray:
    """Drop the third column: 6D = first two columns of the rotation matrix."""
    return mats[..., :, :2].reshape(*mats.shape[:-2], 6)


def sixd_to_matrix(sixd: np.ndarray) -> np.ndarray:
    """Gram-Schmidt decode (Zhou et al. 2019, Eqs. 14-16).

    b1 = N(a1);  b2 = N(a2 - (b1·a2) b1);  b3 = b1 x b2
    """
    a = np.asarray(sixd, dtype=float).reshape(*sixd.shape[:-1], 3, 2)
    a1, a2 = a[..., 0], a[..., 1]

    def _norm(v):
        n = np.linalg.norm(v, axis=-1, keepdims=True)
        return np.divide(v, n, out=np.full_like(v, np.nan), where=n > 1e-12)

    b1 = _norm(a1)
    b2 = _norm(a2 - np.sum(b1 * a2, axis=-1, keepdims=True) * b1)
    b3 = np.cross(b1, b2)
    return np.stack([b1, b2, b3], axis=-1)


def geodesic_error_deg(m1: np.ndarray, m2: np.ndarray) -> np.ndarray:
    """Geodesic angle between rotation matrices (Zhou et al. Eq. 12), in degrees."""
    rel = np.matmul(m1, np.swapaxes(m2, -1, -2))
    trace = np.trace(rel, axis1=-2, axis2=-1)
    return np.degrees(np.arccos(np.clip((trace - 1.0) / 2.0, -1.0, 1.0)))


def angular_velocity_deg_s(rotvec: np.ndarray, frame_rate_hz: float) -> np.ndarray:
    """Finite-difference angular velocity in degrees per second.

    Length matches the input; the first frame is NaN.
    """
    out = np.full_like(rotvec, np.nan)
    out[1:] = np.degrees(np.diff(rotvec, axis=0)) * frame_rate_hz
    return out
