"""Maintenance alerts: RUL-based alert versus a fixed vibration threshold."""

from __future__ import annotations

import numpy as np

from .prognosis import WINDOW, conformal_halfwidth, interval, rul_exponential
from .synth import H_FAIL, Unit


def first_alert_rul(u: Unit, rule) -> int | None:
    """True RUL (days before failure) at the first day the rule fires, or None."""
    for t in range(WINDOW, u.failure_day):
        if rule(u, t):
            return u.failure_day - t
    return None


def rul_rule(lead_days: float, half: float, gate: float = 0.0, persist: int = 1):
    """Fire when the lower bound of the RUL interval is within `lead_days` on `persist` consecutive
    days and the indicator is at least `gate` x H_FAIL (the interval is calibrated for RUL <= 90 days,
    so it is not valid early in life)."""
    def one(u: Unit, t: int) -> bool:
        if u.hi[t] < gate * H_FAIL:
            return False
        p = rul_exponential(u.hi, t)
        return bool(np.isfinite(p) and interval(p, half)[0] <= lead_days)

    def rule(u: Unit, t: int) -> bool:
        return all(one(u, t - k) for k in range(persist) if t - k >= WINDOW)
    return rule


def threshold_rule(fraction: float):
    return lambda u, t: u.hi[t] >= fraction * H_FAIL


def alert_summary(units: list[Unit], rule, min_lead: int = 7, false_alarm_rul: int = 45) -> dict:
    """lead: days before failure of the first alert. False alarm: first alert earlier than
    `false_alarm_rul` days before failure. Missed: no alert at least `min_lead` days before failure."""
    leads = [first_alert_rul(u, rule) for u in units]
    arr = [x for x in leads if x is not None]
    return {
        "n": len(units),
        "no_alert": int(sum(x is None for x in leads)),
        "early_false_alarm_rate": float(np.mean([x is not None and x > false_alarm_rul for x in leads])),
        "missed_rate": float(np.mean([x is None or x < min_lead for x in leads])),
        "median_lead_days": float(np.median(arr)) if arr else None,
    }


def calibrate_rule(cal_units: list[Unit], lead_days: float, alpha: float = 0.1,
                   gates=(0.0, 0.3, 0.5, 0.7), persist: int = 3):
    """Conformal half-width from the calibration units; the gate is the grid value with the lowest
    (early false alarm rate + missed rate) on the same units."""
    from .prognosis import log_ratio_residuals
    half = conformal_halfwidth(log_ratio_residuals(cal_units), alpha)
    best, best_score = gates[0], np.inf
    for g in gates:
        s = alert_summary(cal_units, rul_rule(lead_days, half, g, persist))
        score = s["early_false_alarm_rate"] + s["missed_rate"]
        if score < best_score - 1e-12:
            best, best_score = g, score
    return rul_rule(lead_days, half, best, persist), half, best
