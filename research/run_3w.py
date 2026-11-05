"""Real-data study on the Petrobras 3W dataset (real WELL-* instances only).

usage: python research/run_3w.py /path/to/3w/dataset [cache.pkl]

Normal: class 0 (594 instances). Degradation: class 7 'scaling in PCK' (36 real instances),
whose labels are 0 (normal), then 107 (transient) -- the fault label 7 is reached in only 6 of them.
The task is therefore early detection of the transient onset, NOT remaining-life prediction.
"""

import glob
import json
import os
import pickle
import sys
from pathlib import Path

import numpy as np

from pumpprognosis.health3w import conformal_threshold, first_alert, health_index, persisted

COLS = ["P-PDG", "P-TPT", "T-TPT", "P-MON-CKP", "T-JUS-CKP"]


def load(root: str, cache: str | None):
    if cache and os.path.exists(cache):
        return pickle.load(open(cache, "rb"))
    import pandas as pd

    out = {}
    for cls in (0, 7):
        for f in sorted(glob.glob(f"{root}/{cls}/WELL-*.parquet")):
            d = pd.read_parquet(f, columns=COLS + ["class"])
            out[(cls, os.path.basename(f))] = (
                d[COLS].resample("1min").mean().to_numpy(float),
                d["class"].resample("1min").max().to_numpy(float),
            )
    if cache:
        pickle.dump(out, open(cache, "wb"))
    return out


def stats(items):
    """Per instance: persisted index, onset (first non-zero label) -- None for normals."""
    res = []
    for (cls, name), (x, lab) in items:
        p = persisted(health_index(x))
        if np.isnan(p).all():
            continue
        onset = int(np.argmax(lab > 0)) if (lab > 0).any() else None
        # class-7 files start with a normal stretch; onset must lie after the baseline
        res.append({"cls": cls, "name": name, "well": name.split("_")[0], "p": p, "onset": onset})
    return res


def main():
    root = sys.argv[1]
    cache = sys.argv[2] if len(sys.argv) > 2 else None
    data = load(root, cache)
    allr = stats(data.items())
    normals = [r for r in allr if r["cls"] == 0]
    scal = [r for r in allr if r["cls"] == 7 and r["onset"] is not None]
    # onset must be after baseline+smooth+persist to be evaluable
    scal_ok = [r for r in scal if r["onset"] > 60 + 15 + 10]
    wells = sorted({r["well"] for r in normals})
    rng = np.random.default_rng(0)
    perm = rng.permutation(len(wells))
    cal_w = {wells[i] for i in perm[: len(wells) // 2]}
    cal = [r for r in normals if r["well"] in cal_w]
    tst = [r for r in normals if r["well"] not in cal_w]
    mx = lambda rs: np.array([np.nanmax(r["p"]) for r in rs])
    out = {
        "note": "real 3W WELL instances; 1-min grid; baseline = first 60 min of each instance",
        "n_normal_calibration": len(cal),
        "n_normal_test": len(tst),
        "n_scaling_total": len(scal),
        "n_scaling_evaluable": len(scal_ok),
        "scaling_reached_fault_label": int(
            sum(1 for k, (x, lab) in data.items() if k[0] == 7 and (lab == 7).any())
        ),
        "rules": {},
    }
    rules = {f"conformal_alpha_{a}": conformal_threshold(mx(cal), a) for a in (0.2, 0.1, 0.05)}
    rules.update({f"fixed_z_{z}": float(z) for z in (3, 5, 10, 20)})
    for name, thr in rules.items():
        fa = float(np.mean([first_alert(r["p"], thr) is not None for r in tst]))
        delays, early, miss = [], 0, 0
        for r in scal_ok:
            pre = first_alert(r["p"][: r["onset"]], thr)
            a = first_alert(r["p"], thr)
            if pre is not None:
                early += 1
            if a is None:
                miss += 1
            elif pre is None:
                delays.append(a - r["onset"])
        n = len(scal_ok)
        out["rules"][name] = {
            "threshold_z": thr,
            "false_alarm_rate_normal_test": fa,
            "alert_before_onset_rate": early / n,
            "missed_rate": miss / n,
            "detected_after_onset_n": len(delays),
            "median_delay_min_after_onset": float(np.median(delays)) if delays else None,
            "q90_delay_min": float(np.quantile(delays, 0.9)) if delays else None,
        }
    # exchangeability check: pooled random instance-level split vs well-grouped split
    mxa = mx(normals)
    fas = []
    for k in range(200):
        pm = np.random.default_rng(100 + k).permutation(len(normals))
        c, t = pm[: len(pm) // 2], pm[len(pm) // 2 :]
        fas.append(float(np.mean(mxa[t] > conformal_threshold(mxa[c], 0.1))))
    out["pooled_random_split_alpha_0.1"] = {
        "false_alarm_mean": float(np.mean(fas)),
        "false_alarm_sd": float(np.std(fas)),
    }
    out["median_max_index_by_well"] = {
        w: float(np.median([np.nanmax(r["p"]) for r in normals if r["well"] == w])) for w in wells
    }
    out["scaling_wells_with_normal_instances"] = sorted({r["well"] for r in scal_ok} & set(wells))
    out["scaling_wells_without_normal_instances"] = sorted(
        {r["well"] for r in scal_ok} - set(wells)
    )
    # per-well calibration (wells that have both normals and scaling instances)
    perwell = {}
    for w in out["scaling_wells_with_normal_instances"]:
        nw = [r for r in normals if r["well"] == w]
        pm = np.random.default_rng(7).permutation(len(nw))
        c = [nw[i] for i in pm[: len(nw) // 2]]
        t = [nw[i] for i in pm[len(nw) // 2 :]]
        thr = conformal_threshold(mx(c), 0.1)
        sc = [r for r in scal_ok if r["well"] == w]
        perwell[w] = {
            "n_cal": len(c),
            "n_test_normal": len(t),
            "n_scaling": len(sc),
            "threshold_z": thr,
            "false_alarm_rate_normal_test": float(
                np.mean([first_alert(r["p"], thr) is not None for r in t])
            ),
            "scaling_alert_before_onset": int(
                sum(first_alert(r["p"][: r["onset"]], thr) is not None for r in sc)
            ),
            "scaling_missed": int(sum(first_alert(r["p"], thr) is None for r in sc)),
        }
    out["per_well_calibration_alpha_0.1"] = perwell
    out["normal_test_exposure_min_median"] = float(
        np.median([np.sum(~np.isnan(r["p"])) for r in tst])
    )
    out["scaling_pre_onset_exposure_min_median"] = float(
        np.median([r["onset"] - 85 for r in scal_ok])
    )
    Path(__file__).with_name("results_3w.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
