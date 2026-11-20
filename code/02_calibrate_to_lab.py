#!/usr/bin/env python3
"""Step 2: calibrate the two least-known inputs against the measured UNI laboratory results.

Plain-language summary: the USGS library has no coal and no foundry-grade red
iron oxide, and nobody knows the "effective" particle size of seacoal and
pigment once they are mixed into sand. This script picks those two sizes so the
computed spectra reproduce the 24 measured AUC values in Kuubata (2025). It
also compares every candidate stand-in spectrum, and tests how stable the
fitted sizes are when one DC2 group is left out.

Treatment of the shared baseline: within each DC2 group, all AUC values are
computed against the same single 0% additive spectrum (and the seacoal and red
iron oxide series share that spectrum). Any difference between that one
baseline measurement and the additive samples (packing, session, reference)
shifts all six AUC values in the group by the same amount. The fit therefore
includes one free offset per DC2 group (4 offsets for 24 values). The fitted
offsets are reported; they are a finding, not a nuisance to hide.

Outputs: data/processed/lab_calibration.json, data/processed/lab_calibration_candidates.csv,
         data/processed/lab_calibration_fit.csv, paper/stats.json (lab_calibration section)
"""

import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
PROC = os.path.join(ROOT, "data", "processed")
STATS = os.path.join(ROOT, "paper", "stats.json")


def load_lab(rules):
    lab = pd.read_csv(os.path.join(ROOT, rules["lab_calibration"]["data"]))
    lab = lab[lab.additive_pct > 0].copy()
    lab["add"] = lab.additive.map({"Seacoal": "seacoal", "Red Iron Oxide": "iron_oxide"})
    return lab.reset_index(drop=True)


def auc_curves(E, ins, add, grid, model):
    """AUC for the 12 lab mixtures of one additive at each candidate grain size: (len(grid), 12)."""
    out = []
    for d in grid:
        gr = dict(E.grain_um)
        gr[add] = d
        gr = {k: (v if v not in ("fit", "lab_fit") else 10.0) for k, v in gr.items()}
        tab = g.lab.lab_auc_table(E, ins, gr, model)
        out.append(tab[tab.additive == add].AUC.to_numpy())
    return np.array(out)


def fit_offsets(lab_vals, pred, dc):
    off = {int(k): float(np.mean((lab_vals - pred)[dc == k])) for k in np.unique(dc)}
    res = lab_vals - pred - np.array([off[int(k)] for k in dc])
    return float(np.sqrt(np.mean(res ** 2))), off, res


def joint_fit(curves_sc, curves_fe, lab, grid, mask=None):
    mask = np.ones(len(lab), bool) if mask is None else mask
    y = lab.AUC.to_numpy()
    dc = lab.dc2_pct.to_numpy()
    is_sc = (lab["add"] == "seacoal").to_numpy()
    best = None
    for i in range(len(grid)):
        for j in range(len(grid)):
            pred = np.empty(len(lab))
            pred[is_sc] = curves_sc[i]
            pred[~is_sc] = curves_fe[j]
            r, off, _ = fit_offsets(y[mask], pred[mask], dc[mask])
            if best is None or r < best[0]:
                best = (r, i, j, off, pred)
    return best


def main():
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    lab = load_lab(rules)
    os.makedirs(PROC, exist_ok=True)
    cfg = rules["lab_calibration"]["grid_um"]
    grid = np.geomspace(cfg["start"], cfg["stop"], cfg["n"])
    model = rules["mixing_model"]
    y = lab.AUC.to_numpy()

    # candidate comparison: every seacoal stand-in x every iron oxide stand-in
    sc_c = {"default": None, **rules["components"]["seacoal"].get("alternatives", {})}
    fe_c = {"default": None, **rules["components"]["iron_oxide"].get("alternatives", {})}
    cand_rows, cache = [], {}
    for sname, sfile in sc_c.items():
        ov = {"seacoal": {"spectrum": sfile}} if sfile else {}
        E = g.io.load_endmembers(rules, RAW, ov)
        ins = g.instrument.Instrument(rules, E.wl)
        cache[("sc", sname)] = auc_curves(E, ins, "seacoal", grid, model)
    for fname, ffile in fe_c.items():
        ov = {"iron_oxide": {"spectrum": ffile}} if ffile else {}
        E = g.io.load_endmembers(rules, RAW, ov)
        ins = g.instrument.Instrument(rules, E.wl)
        cache[("fe", fname)] = auc_curves(E, ins, "iron_oxide", grid, model)
    for sname in sc_c:
        for fname in fe_c:
            r, i, j, off, _ = joint_fit(cache[("sc", sname)], cache[("fe", fname)], lab, grid)
            # also without offsets, for reference
            pred = np.concatenate([cache[("sc", sname)][i], cache[("fe", fname)][j]])
            r_no = float(np.sqrt(np.mean((y - pred) ** 2)))
            cand_rows.append({"seacoal_spectrum": sname if sname != "default" else rules["components"]["seacoal"]["spectrum"],
                              "iron_oxide_spectrum": fname if fname != "default" else rules["components"]["iron_oxide"]["spectrum"],
                              "seacoal_um": round(float(grid[i]), 2), "iron_oxide_um": round(float(grid[j]), 2),
                              "rmse_with_offsets": round(r, 1), "rmse_same_sizes_no_offsets": round(r_no, 1),
                              "max_iron_oxide_auc": round(float(cache[("fe", fname)].max()), 1)})
    cand = pd.DataFrame(cand_rows)
    cand.to_csv(os.path.join(PROC, "lab_calibration_candidates.csv"), index=False)
    print(cand.to_string())

    # chosen spectra (the defaults in the rules file)
    r, i, j, off, pred = joint_fit(cache[("sc", "default")], cache[("fe", "default")], lab, grid)
    dc = lab.dc2_pct.to_numpy()
    _, _, res = fit_offsets(y, pred, dc)
    fit = lab[["sample_id", "add", "dc2_pct", "additive_pct", "AUC"]].copy()
    fit["model_AUC"] = pred.round(1)
    fit["group_offset"] = [round(off[int(k)], 1) for k in dc]
    fit["model_plus_offset"] = (pred + fit["group_offset"]).round(1)
    fit["residual"] = res.round(1)
    fit.to_csv(os.path.join(PROC, "lab_calibration_fit.csv"), index=False)

    # stability: leave one DC2 group out
    loo = []
    for k in (3, 6, 9, 12):
        rr, ii, jj, _, _ = joint_fit(cache[("sc", "default")], cache[("fe", "default")], lab, grid, dc != k)
        loo.append({"left_out_dc2": k, "seacoal_um": round(float(grid[ii]), 2), "iron_oxide_um": round(float(grid[jj]), 2),
                    "rmse": round(rr, 1)})
    r_offsets_only, _, _ = fit_offsets(y, np.zeros(len(y)), dc)
    result = {
        "seacoal_um": round(float(grid[i]), 2), "iron_oxide_um": round(float(grid[j]), 2),
        "rmse_with_offsets": round(r, 1), "rmse_offsets_only_no_additive_model": round(r_offsets_only, 1),
        "lab_auc_sd": round(float(y.std()), 1), "lab_auc_range": [round(float(y.min()), 1), round(float(y.max()), 1)],
        "group_offsets": {str(k): round(v, 1) for k, v in off.items()},
        "leave_one_group_out": loo,
        "n_lab_values": int(len(y)), "grid_um": [cfg["start"], cfg["stop"], cfg["n"]],
        "seacoal_spectrum": rules["components"]["seacoal"]["spectrum"],
        "iron_oxide_spectrum": rules["components"]["iron_oxide"]["spectrum"],
    }
    json.dump(result, open(os.path.join(PROC, "lab_calibration.json"), "w"), indent=2)
    print(json.dumps(result, indent=2))
    stats = json.load(open(STATS)) if os.path.exists(STATS) else {}
    stats["lab_calibration"] = result
    stats["lab_calibration_candidates"] = cand_rows
    os.makedirs(os.path.dirname(STATS), exist_ok=True)
    json.dump(stats, open(STATS, "w"), indent=2)


if __name__ == "__main__":
    main()
