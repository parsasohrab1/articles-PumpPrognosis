"""RUL estimation from a window of the health indicator, with split-conformal intervals."""

from __future__ import annotations

import numpy as np

from .synth import H0, H_FAIL, Unit

WINDOW = 60                   # chosen on separate selection units, see research/run_study.py


def rul_exponential(hi: np.ndarray, t: int, window: int = WINDOW) -> float:
    """Fit log(HI - H0) = c + lambda t on the last `window` days and extrapolate to H_FAIL."""
    seg = hi[max(0, t - window + 1):t + 1]
    y = np.log(np.clip(seg - H0, 1e-3, None))
    x = np.arange(len(seg))
    lam, _c = np.polyfit(x, y, 1)
    if lam <= 1e-6:
        return float("inf")
    return max(0.0, float((np.log(H_FAIL - H0) - y[-1]) / lam))


def rul_linear(hi: np.ndarray, t: int, window: int = WINDOW) -> float:
    """Baseline: straight-line extrapolation of the last window."""
    seg = hi[max(0, t - window + 1):t + 1]
    slope = np.polyfit(np.arange(len(seg)), seg, 1)[0]
    if slope <= 1e-6:
        return float("inf")
    return max(0.0, float((H_FAIL - seg[-1]) / slope))


def eval_points(u: Unit, max_rul: int = 90, min_rul: int = 1):
    """Days at which the true RUL lies in [min_rul, max_rul] and a full window is available."""
    for t in range(max(WINDOW, u.failure_day - max_rul), u.failure_day - min_rul + 1):
        yield t, u.failure_day - t


def log_ratio_residuals(units: list[Unit], estimator=rul_exponential) -> np.ndarray:
    """log(predicted RUL) - log(true RUL) over the evaluation points."""
    res = []
    for u in units:
        for t, true in eval_points(u):
            p = estimator(u.hi, t)
            if np.isfinite(p) and p > 0:
                res.append(np.log(p) - np.log(true))
    return np.array(res)


def conformal_halfwidth(residuals: np.ndarray, alpha: float = 0.1) -> float:
    r = np.sort(np.abs(residuals))
    k = int(np.ceil((len(r) + 1) * (1 - alpha)))
    return float(r[min(k, len(r)) - 1])


def interval(pred: float, half: float) -> tuple[float, float]:
    return pred * np.exp(-half), pred * np.exp(half)


def coverage(units: list[Unit], half: float, estimator=rul_exponential) -> float:
    hit = n = 0
    for u in units:
        for t, true in eval_points(u):
            p = estimator(u.hi, t)
            if not np.isfinite(p) or p <= 0:
                continue
            lo, hi = interval(p, half)
            hit += lo <= true <= hi
            n += 1
    return hit / n


def mae_days(units: list[Unit], estimator, max_rul: int = 90) -> float:
    err = []
    for u in units:
        for t, true in eval_points(u, max_rul):
            p = estimator(u.hi, t)
            if np.isfinite(p):
                err.append(abs(p - true))
    return float(np.mean(err))
