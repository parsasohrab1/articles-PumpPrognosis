"""RUL prognosis and maintenance-alert study on synthetic pump run-to-failure series.

Usage: python research/run_study.py --out research/results.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pumpprognosis.alerts import alert_summary, calibrate_rule, threshold_rule
from pumpprognosis.prognosis import (
    conformal_halfwidth,
    coverage,
    log_ratio_residuals,
    mae_days,
    rul_exponential,
    rul_linear,
)
from pumpprognosis.synth import make_units


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="research/results.json")
    a = ap.parse_args()
    # window length chosen on separate selection units (not the calibration or test units)
    sel = make_units(80, np.random.default_rng(9))
    window_table = {}
    for w in (30, 60, 120, 240):
        def est(hi, t, w=w):
            return rul_exponential(hi, t, w)
        window_table[w] = mae_days(sel, est)
    cal = make_units(150, np.random.default_rng(1))
    half = conformal_halfwidth(log_ratio_residuals(cal), 0.1)
    out = {"note": "synthetic run-to-failure series; RUL evaluated 1 to 90 days before failure",
           "window_selection_mae_days": {str(k): v for k, v in window_table.items()},
           "conformal_half_width_log": half, "n_calibration_units": len(cal)}
    settings = {"same_conditions": 1.0, "faster_wear_x1.5": 1.5, "slower_wear_x0.7": 0.7}
    for name, scale in settings.items():
        test = make_units(150, np.random.default_rng(2), rate_scale=scale)
        rule, _, gate = calibrate_rule(cal, lead_days=14)
        out[name] = {
            "n_units": len(test), "alert_gate_fraction": gate,
            "rul_mae_days_exponential": mae_days(test, rul_exponential),
            "rul_mae_days_linear": mae_days(test, rul_linear),
            "interval_coverage_target_0.90": coverage(test, half),
            "alert_rul_conformal": alert_summary(test, rule),
            "alert_threshold_0.5": alert_summary(test, threshold_rule(0.5)),
            "alert_threshold_0.7": alert_summary(test, threshold_rule(0.7)),
            "alert_threshold_0.9": alert_summary(test, threshold_rule(0.9))}
    Path(a.out).write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
