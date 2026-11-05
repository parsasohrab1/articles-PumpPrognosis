import numpy as np

from pumpprognosis.health3w import conformal_threshold, first_alert, health_index, persisted


def _series(n=400, drift_at=None, seed=0):
    rng = np.random.default_rng(seed)
    x = 100 + rng.normal(0, 1, (n, 3))
    if drift_at:
        x[drift_at:, 0] += np.linspace(0, 30, n - drift_at)
    return x


def test_index_flat_for_stationary_series():
    hi = health_index(_series())
    assert np.nanmax(hi) < 6


def test_index_rises_with_drift_and_alert_after_onset():
    x = _series(drift_at=200)
    p = persisted(health_index(x))
    a = first_alert(p, 6.0)
    assert a is not None and a >= 200


def test_conformal_threshold_quantile():
    s = np.arange(1.0, 100.0)
    assert conformal_threshold(s, 0.1) == 90.0
    assert conformal_threshold(s[:5], 0.01) == float("inf")


def test_all_nan_columns_ignored():
    x = _series()
    x[:, 2] = np.nan
    assert np.isfinite(np.nanmax(health_index(x)))
