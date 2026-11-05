"""Health index and conformal alert for real well-sensor series (3W dataset, 1-min grid).

Not a remaining-useful-life model: 3W labels give the onset of a transient, not a failure time.
"""

from __future__ import annotations

import numpy as np

BASE = 60  # minutes used as the per-instance healthy baseline
SMOOTH = 15  # minutes, rolling median
PERSIST = 10  # minutes the index must stay above the threshold


def _rolling_median(x: np.ndarray, w: int) -> np.ndarray:
    n = len(x)
    out = np.full(n, np.nan)
    for i in range(w - 1, n):
        seg = x[i - w + 1 : i + 1]
        seg = seg[~np.isnan(seg)]
        if len(seg) > w // 2:
            out[i] = np.median(seg)
    return out


def usable_columns(x: np.ndarray, max_nan: float = 0.2) -> list[int]:
    return [j for j in range(x.shape[1]) if np.isnan(x[:, j]).mean() <= max_nan]


def health_index(x: np.ndarray, base: int = BASE, smooth: int = SMOOTH) -> np.ndarray:
    """Max over usable variables of |robust z| against the first ``base`` minutes."""
    cols = usable_columns(x)
    if not cols or len(x) <= base + smooth:
        return np.full(len(x), np.nan)
    z = []
    for j in cols:
        b = x[:base, j]
        b = b[~np.isnan(b)]
        if len(b) < base // 2:
            continue
        mu = np.median(b)
        sd = 1.4826 * np.median(np.abs(b - mu))
        sd = max(sd, 1e-3 * max(abs(mu), 1e-9), 1e-9)
        z.append(np.abs(_rolling_median(x[:, j], smooth) - mu) / sd)
    if not z:
        return np.full(len(x), np.nan)
    hi = np.nanmax(np.vstack(z), axis=0)
    hi[: base + smooth] = np.nan
    return hi


def persisted(hi: np.ndarray, persist: int = PERSIST) -> np.ndarray:
    """Running minimum of the index over ``persist`` minutes (above thr for that long)."""
    out = np.full(len(hi), np.nan)
    for i in range(persist - 1, len(hi)):
        seg = hi[i - persist + 1 : i + 1]
        if not np.isnan(seg).any():
            out[i] = seg.min()
    return out


def conformal_threshold(max_stats: np.ndarray, alpha: float) -> float:
    """Split-conformal threshold: instance-level false-alarm rate <= alpha (exchangeable normals)."""
    n = len(max_stats)
    k = int(np.ceil((n + 1) * (1 - alpha)))
    s = np.sort(max_stats)
    return float(s[min(k, n) - 1]) if k <= n else float("inf")


def first_alert(p: np.ndarray, thr: float) -> int | None:
    idx = np.where(p > thr)[0]
    return int(idx[0]) if len(idx) else None
