# Software Requirements Specification – PumpPrognosis

- SR-1 `rul_exponential(hi, t, window)` fits log health index over the last `window` (=60) days and extrapolates to the failure level (`H_FAIL`=10).
- SR-2 `rul_linear` is the baseline using the same window.
- SR-3 `conformal_halfwidth` computes a split-conformal half-width on log-ratio residuals from calibration units; `interval` applies it; `coverage` measures it.
- SR-4 `calibrate_rule(cal_units, lead_days, alpha=0.1, gates=(0,0.3,0.5,0.7), persist=3)` returns the alert rule, half-width and gate chosen on calibration units only.
- SR-5 `threshold_rule` implements fixed health-index thresholds (0.5/0.7/0.9 of failure level) as comparators.
- SR-6 The window is selected on units separate from calibration and test units (different seeds).
- SR-7 Tests cover RUL on a noiseless trend, interval coverage helper, alert rules and calibration (7 tests).
