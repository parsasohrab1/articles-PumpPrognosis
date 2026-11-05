import numpy as np
import pytest

from pumpprognosis.alerts import alert_summary, calibrate_rule, first_alert_rul, threshold_rule
from pumpprognosis.prognosis import (
    conformal_halfwidth,
    coverage,
    eval_points,
    interval,
    log_ratio_residuals,
    rul_exponential,
    rul_linear,
)
from pumpprognosis.synth import H0, H_FAIL, make_units


def test_units_are_seeded_and_end_at_failure_level():
    a = make_units(5, np.random.default_rng(1))
    b = make_units(5, np.random.default_rng(1))
    assert all(np.array_equal(x.hi, y.hi) for x, y in zip(a, b, strict=True))
    assert all(u.failure_day == len(u.hi) - 1 for u in a)
    assert all(u.hi[0] > H0 * 0.5 for u in a)


def test_exponential_rul_exact_on_noise_free_curve():
    t = np.arange(200)
    lam, a = 0.02, 0.1
    hi = H0 + a * np.exp(lam * t)
    t_fail = np.log((H_FAIL - H0) / a) / lam
    assert rul_exponential(hi, 150) == pytest.approx(t_fail - 150, rel=1e-3)


def test_flat_series_gives_infinite_rul():
    hi = np.full(100, 3.0)
    assert rul_exponential(hi, 80) == float("inf") and rul_linear(hi, 80) == float("inf")


def test_exponential_beats_linear_extrapolation():
    units = make_units(30, np.random.default_rng(2))
    e = np.abs(log_ratio_residuals(units)).mean()
    lin = np.abs(log_ratio_residuals(units, rul_linear)).mean()
    assert e < lin


def test_eval_points_have_true_rul_in_range():
    u = make_units(1, np.random.default_rng(3))[0]
    assert all(1 <= r <= 90 for _, r in eval_points(u))


def test_conformal_coverage_on_new_units():
    cal = make_units(60, np.random.default_rng(4))
    test = make_units(60, np.random.default_rng(5))
    half = conformal_halfwidth(log_ratio_residuals(cal), 0.1)
    assert 0.8 <= coverage(test, half) <= 0.97
    lo, hi = interval(10.0, half)
    assert lo < 10.0 < hi


def test_alert_rules_run_and_conformal_alert_precedes_failure():
    cal = make_units(60, np.random.default_rng(6))
    test = make_units(30, np.random.default_rng(7))
    rule, half, gate = calibrate_rule(cal, lead_days=14)
    s = alert_summary(test, rule)
    assert s["n"] == len(test) and half > 0 and 0.0 <= gate <= 0.7
    leads = [first_alert_rul(u, rule) for u in test]
    assert all(x is None or x >= 1 for x in leads)
    t = alert_summary(test, threshold_rule(0.7))
    assert 0.0 <= t["missed_rate"] <= 1.0
