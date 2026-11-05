# articles-PumpPrognosis

Remaining-useful-life (RUL) prognosis and conformal alerting for pumps from a
health-index series. TRL 4 (laboratory validation on a **synthetic** twin only).

- `src/pumpprognosis/` – exponential-trend RUL, linear baseline, split-conformal
  interval, alert rules (RUL-based and fixed-threshold).
- `research/run_study.py` – window selection, calibration and test on separate
  synthetic units, including two shifted wear conditions; writes `research/results.json`.
- `tests/` – unit tests (`pytest`).
- `docs/` – BRS, SRS, TRL assessment.

```
pip install -e .[dev] && pytest && python research/run_study.py
```

**Limitation:** all numbers come from a synthetic run-to-failure generator.
No field pump data have been used; no claim about real equipment is made.
