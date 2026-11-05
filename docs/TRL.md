# TRL assessment – PumpPrognosis

**Claimed level: TRL 4** (component validated in a laboratory/simulated environment).

Evidence (`research/results.json`, 150 test units per condition, synthetic):

| Condition | RUL MAE exp. / linear (days) | Interval coverage (target 0.90) | Conformal alert: early false alarm / missed / median lead (d) | Threshold 0.9: early FA / missed / lead |
|---|---|---|---|---|
| Same as calibration | 18.2 / 66.9 | 0.898 | 0.167 / 0.007 / 32 | 0.293 / 0.007 / 34 |
| Wear ×1.5 | 14.9 / 108.3 | 0.932 | 0.040 / 0.013 / 21 | 0.040 / 0.067 / 20 |
| Wear ×0.7 | 24.7 / 50.5 | 0.847 | 0.315 / 0.000 / 38 | 0.616 / 0.000 / 53 |

Honest notes:
- Coverage drops below target (0.847) under slower wear; early false alarms rise to 31.5 %.
- Window (60 d) was chosen on separate units; with 30 d the MAE was 96 d. Gate fraction (0.7) was chosen on calibration units, which is a tuning step.
- Everything is synthetic; the generator was written by the authors, so results show method behaviour, not field performance.

Not reached for TRL 5: validation on real pump data in a relevant environment.
