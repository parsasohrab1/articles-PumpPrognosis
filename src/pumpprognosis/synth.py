"""Synthetic pump run-to-failure series (labelled synthetic, not field data)."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

H0, H_FAIL = 2.0, 10.0           # baseline and failure level of the health indicator (vibration, mm/s)


@dataclass
class Unit:
    hi: np.ndarray               # daily health indicator, ends at the failure day
    failure_day: int             # index of the failure (len(hi) - 1)


def make_units(n: int, rng: np.random.Generator, rate_scale: float = 1.0,
               noise: float = 0.15, max_days: int = 900) -> list[Unit]:
    """HI(t) = H0 + a exp(lambda t) * noise; the pump fails when the noise-free level reaches H_FAIL.
    lambda is lognormal across units; `rate_scale` multiplies it (a shift in operating conditions)."""
    units = []
    for _ in range(n):
        lam = rate_scale * float(rng.lognormal(np.log(0.012), 0.35))
        a = float(rng.uniform(0.05, 0.3))
        t_fail = int(np.log((H_FAIL - H0) / a) / lam)
        if t_fail < 60 or t_fail > max_days:
            continue
        t = np.arange(t_fail + 1)
        clean = H0 + a * np.exp(lam * t)
        hi = clean * np.exp(rng.normal(0.0, noise, len(t)))
        units.append(Unit(hi, t_fail))
    return units
