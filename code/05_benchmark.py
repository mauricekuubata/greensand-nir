#!/usr/bin/env python3
"""Step 5: build the detection-limit benchmark sets, score the baseline methods, write the leaderboard.

Plain-language summary: for each additive (seacoal, red iron oxide), each sand
condition (dry, moist) and each noise level (ideal, lab, plant floor), this
script makes a training set and a test set of simulated instrument readings
with everything else in the sand varying across production ranges. Five
standard methods are trained and scored with one fixed rule (see
src/greensand_nir/benchmark.py): the detection limit is the lowest additive
level caught at least 95% of the time while clean sand raises a false alarm at
most 5% of the time. Results go to benchmark/leaderboard.csv and the public
leaderboard page docs/leaderboard/index.html.

Anyone can add a method: train on benchmark/sets/<set>_calibration.csv.gz,
write one score per row of <set>_test.csv.gz, and run code/score_submission.py.

Outputs: benchmark/sets/*, benchmark/leaderboard.csv, benchmark/power_curves.csv,
         benchmark/sensitivity.csv, paper/stats.json (benchmark section)
"""

import argparse
import json
import os
import sys
import time

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402
from greensand_nir.compositions import ORDER  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
PROC = os.path.join(ROOT, "data", "processed")
BENCH = os.path.join(ROOT, "benchmark")
STATS = os.path.join(ROOT, "paper", "stats.json")

N_CAL = 600
CAL_BLANK_SHARE = 0.25
N_TEST_BLANK = 200
N_TEST_PER_LEVEL = 100
TRACKS = {"dry": (0.0, 0.0), "moist": (2.0, 5.0)}
RANGES = {"seacoal": (0.0, 5.0), "iron_oxide": (0.0, 2.0)}
SET_VERSION = "1.0"


def calibrated_endmembers(rules, overrides=None, cal=None):
    E = g.io.load_endmembers(rules, RAW, overrides)
    for comp in ("seacoal", "iron_oxide"):
        if isinstance(E.grain_um[comp], str):
            E.grain_um[comp] = float(cal[f"{comp}_um"]) if cal else float(rules["components"][comp]["grain_um_fallback"])
    return E


def spectra(E, rules, ins, comps, tier, rng, model=None, path_factor=None):
    m = g.compositions.mass_fractions(comps, ORDER)
    moist = comps["moisture_pct"].to_numpy()
    R = g.mixing.mix(E.matrix(list(ORDER)), m, [E.density[o] for o in ORDER], [E.grain_um[o] for o in ORDER],
                     model=model or rules["mixing_model"], moisture_pct=moist if moist.max() > 0 else None,
                     water_alpha=E.water_alpha,
                     path_factor=rules["water"]["path_factor"] if path_factor is None else path_factor)
    return ins.measure(R, tier, rng)


def make_set(E, rules, ins, target, track, tier, seed, model=None, path_factor=None):
    rng = np.random.default_rng(seed)
    lo, hi = RANGES[target]
    levels = g.benchmark.LEVELS[target]
    others = {k: v for k, v in RANGES.items() if k != target}
    kw = {f"{k}": v for k, v in others.items()}
    # calibration set: 25% blanks, the rest log-uniform between the lowest test level and the maximum
    n_blank = int(N_CAL * CAL_BLANK_SHARE)
    tgt = np.concatenate([np.zeros(n_blank),
                          np.exp(rng.uniform(np.log(levels[0]), np.log(hi), N_CAL - n_blank))])
    rng.shuffle(tgt)
    cal = g.compositions.random_compositions(N_CAL, rng, moisture=TRACKS[track], **kw)
    cal[f"{target}_pct"] = tgt
    cal["silica_sand_pct"] = 100 - cal.clay_pct - cal.seacoal_pct - cal.iron_oxide_pct
    # test set: blanks plus fixed levels
    tl = np.concatenate([np.zeros(N_TEST_BLANK), np.repeat(levels, N_TEST_PER_LEVEL)])
    test = g.compositions.random_compositions(len(tl), rng, moisture=TRACKS[track], **kw)
    test[f"{target}_pct"] = tl
    test["silica_sand_pct"] = 100 - test.clay_pct - test.seacoal_pct - test.iron_oxide_pct
    Rc = spectra(E, rules, ins, cal, tier, rng, model, path_factor)
    Rt = spectra(E, rules, ins, test, tier, rng, model, path_factor)
    return cal, Rc, test, Rt


def save_set(name, cal, Rc, test, Rt, centers):
    os.makedirs(os.path.join(BENCH, "sets"), exist_ok=True)
    cols = [f"R_{w:.2f}" for w in centers]
    for part, comp, R in (("calibration", cal, Rc), ("test", test, Rt)):
        df = comp.round(4).reset_index(drop=True)
        df.insert(0, "sample_id", [f"{name}-{part[:3]}-{i:05d}" for i in range(len(df))])
        df = pd.concat([df, pd.DataFrame(R.round(5), columns=cols)], axis=1)
        df.to_csv(os.path.join(BENCH, "sets", f"{name}_{part}.csv.gz"), index=False,
                  compression={"method": "gzip", "mtime": 0})


def evaluate(method_factory, Rc, yc, Rt, yt):
    t0 = time.time()
    m = method_factory().fit(Rc, yc)
    s = m.score(Rt)
    tab, lod, thr, det = g.benchmark.score_levels(s, yt, details=True)
    extra = dict(det)
    if hasattr(m, "res"):
        extra.update({"n_components": m.res["n_components"], "rmsecv": round(m.res["rmsecv"], 4),
                      "r2cv": round(m.res["r2cv"], 4)})
    return tab, lod, round(time.time() - t0, 1), extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-sensitivity", action="store_true")
    a = ap.parse_args()
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    cal_info = json.load(open(os.path.join(PROC, "lab_calibration.json")))
    E = calibrated_endmembers(rules, cal=cal_info)
    ins = g.instrument.Instrument(rules, E.wl)
    methods = g.benchmark.baselines()

    board, curves = [], []
    seed = 1000
    for track in TRACKS:
        for tier in rules["noise_tiers"]:
            for target in RANGES:
                seed += 1
                name = f"GSNIR-bench-v{SET_VERSION}_{track}_{tier}_{target}"
                cal, Rc, test, Rt = make_set(E, rules, ins, target, track, tier, seed)
                save_set(name, cal, Rc, test, Rt, ins.centers)
                yc, yt = cal[f"{target}_pct"].to_numpy(), test[f"{target}_pct"].to_numpy()
                for mname, fac in methods.items():
                    tab, lod, secs, extra = evaluate(fac, Rc, yc, Rt, yt)
                    board.append({"set": name, "track": track, "tier": tier, "target": target, "method": mname,
                                  "detection_limit_pct": lod, "submitted_by": "baseline (greensand-nir v1.0)",
                                  "seconds": secs, **extra})
                    for _, r in tab.iterrows():
                        curves.append({"track": track, "tier": tier, "target": target, "method": mname,
                                       "level": r.level, "power": r.power})
                    print(f"{track:5s} {tier:5s} {target:10s} {mname:16s} LOD={lod}  ({secs}s) {extra}")
    lb = pd.DataFrame(board)
    lb.to_csv(os.path.join(BENCH, "leaderboard.csv"), index=False)
    pd.DataFrame(curves).to_csv(os.path.join(BENCH, "power_curves.csv"), index=False)

    # sensitivity of the PLSR detection limit to each modelling assumption (dry, lab tier)
    sens = []
    if not a.skip_sensitivity:
        scen = {
            "calibrated default": dict(),
            "USGS priors (no lab calibration)": dict(cal=None),
            "linear mixing": dict(model="linear"),
            "seacoal = carbon black": dict(ov={"seacoal": {"spectrum": rules["components"]["seacoal"]["alternatives"]["carbon_black"],
                                                            "grain_um": cal_info["seacoal_um"]}}),
            "clay = calcium montmorillonite SAz-1": dict(ov={"clay": {"spectrum": rules["components"]["clay"]["alternatives"]["calcium_bentonite"]}}),
            "clay grain 30 um": dict(ov={"clay": {"grain_um": 30}}),
            "instrument FWHM 25 nm": dict(fwhm=25),
        }
        for sname, sc in scen.items():
            Es = calibrated_endmembers(rules, sc.get("ov"), cal_info if "cal" not in sc else sc["cal"])
            r2 = json.loads(json.dumps(rules))
            if "fwhm" in sc:
                r2["instrument"]["fwhm_nm"] = sc["fwhm"]
            ins2 = g.instrument.Instrument(r2, Es.wl)
            for target in RANGES:
                for track, pf in (("dry", None), ("moist", None), ("moist", 4.0)):
                    if track == "moist" and sname != "calibrated default":
                        continue
                    cal, Rc, test, Rt = make_set(Es, r2, ins2, target, track, "lab", 5000 + len(sens),
                                                 sc.get("model"), pf)
                    tab, lod, _, extra = evaluate(methods["PLSR"], Rc, cal[f"{target}_pct"].to_numpy(),
                                                  Rt, test[f"{target}_pct"].to_numpy())
                    label = sname if pf is None else f"{sname}, water path factor 4"
                    sens.append({"scenario": label, "track": track, "target": target, "PLSR_detection_limit_pct": lod,
                                 **{k: v for k, v in extra.items() if k in ("n_components", "rmsecv", "r2cv")}})
                    print("SENS", label, track, target, lod, extra)
        pd.DataFrame(sens).to_csv(os.path.join(BENCH, "sensitivity.csv"), index=False)

    stats = json.load(open(STATS))
    best = (lb.dropna(subset=["detection_limit_pct"]).sort_values("detection_limit_pct")
            .groupby(["track", "tier", "target"]).first().reset_index())
    stats["benchmark"] = {
        "set_version": SET_VERSION, "n_cal": N_CAL, "n_test_blank": N_TEST_BLANK, "n_test_per_level": N_TEST_PER_LEVEL,
        "levels": g.benchmark.LEVELS, "alpha": g.benchmark.ALPHA, "power": g.benchmark.POWER,
        "tiers": rules["noise_tiers"], "tracks": {k: list(v) for k, v in TRACKS.items()},
        "leaderboard": board, "best": best[["track", "tier", "target", "method", "detection_limit_pct"]].to_dict("records"),
        "sensitivity": sens,
    }
    json.dump(stats, open(STATS, "w"), indent=2, default=float)


if __name__ == "__main__":
    main()
