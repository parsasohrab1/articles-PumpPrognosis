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

## Real-data check on Petrobras 3W (added)

Data: public 3W v2.0.0, **real `WELL-*` instances only** (594 normal, 36 "scaling in the production choke", class 7).
3W holds offshore oil-well sensor data, **not ESP pump run-to-failure data**, and its labels give the onset of a
transient (label 107), not a failure time (fault label 7 is reached in only 5 of the 36 instances).
RUL therefore cannot be evaluated on it; the real-data test covers only the health-index + conformal-alert part
(`research/run_3w.py`, `research/results_3w.json`, `src/pumpprognosis/health3w.py`).

| Result | Value |
|---|---|
| Conformal threshold, pooled random instance split (α = 0.1) | false-alarm rate on held-out normals 0.096 ± 0.027 – the guarantee holds when instances are exchangeable |
| Same threshold, calibration and test split by **well** (α = 0.1) | false-alarm rate 0.56 – the guarantee fails; wells differ strongly (median max index 0.6 to 10.4, one well 530) |
| Scaling instances, well-split threshold (α = 0.1, z ≈ 4.5) | alert before transient onset in 39 %, missed 8 %, median delay after onset 687 min |
| Fixed z = 5 | false-alarm rate 0.53, missed 14 %, median delay 542 min |
| Per-well calibration (only wells 1 and 6 have both normal and scaling data) | well 1: false-alarm 0.15, 1 scaling instance, not alerted before onset; well 6: false-alarm 0.04, threshold z = 481, 2 scaling instances both missed |

Conclusions:
- The index cannot separate early scaling from normal behaviour on real wells with a 60-minute self-baseline; alerts that
  occur before onset are false alarms by definition, and detections come hours after onset.
- Calibration must be per well; four of the six scaling wells (21–24) have no normal instances in 3W, so it cannot be checked there.
- Per-well results rest on 3 scaling instances and are anecdotal. **TRL stays 4 (synthetic); no TRL 5 claim.**
- The ESP wording in the article must be removed or replaced by "gradual-degradation of oil-well production choke".
