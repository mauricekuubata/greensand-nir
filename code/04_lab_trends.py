#!/usr/bin/env python3
"""Step 4: repeat the Kuubata (2025) laboratory analysis on computed spectra and compare.

Plain-language summary: this script builds the same 32 dry mixtures the UNI
study measured, "measures" them with the simulated instrument (lab noise
level), and runs exactly the same analysis as the study's R code: PCA on
centred, scaled absorbance (1000-2350 nm), and relative AUC against the 0%
additive sample at each DC2 level. It then checks five measured trends and
compares the computed AUC values with the measured ones.

Trends checked (from the paper):
  T1 PC1 explains more than 95% of variance in both series (lab: 99.23% seacoal, 97.87% red iron oxide)
  T2 PC1 score rises with seacoal; T3 PC1 score rises with red iron oxide
  T4 AUC rises with additive level within every DC2 group
  T5 the seacoal series reaches larger AUC values than the red iron oxide series

Variants: the calibrated default, the USGS-only priors (no lab calibration),
and linear mixing, so the effect of each modelling choice is visible.

Outputs: data/processed/lab_trends.csv, data/processed/lab_auc_comparison.csv, paper/stats.json
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
PROC = os.path.join(ROOT, "data", "processed")
STATS = os.path.join(ROOT, "paper", "stats.json")
LAB_PC1 = {"seacoal": 99.23, "iron_oxide": 97.87}
N_REPEATS = 50  # independent noise draws of the whole 32-sample experiment


def run_variant(E, ins, grains, model, rng):
    pc1, t2, t3, t4, t5, aucs = {"seacoal": [], "iron_oxide": []}, [], [], [], [], []
    for _ in range(N_REPEATS):
        tab = []
        for add in ("seacoal", "iron_oxide"):
            d, Ri = g.lab.simulate(E, ins, add, grains, model, tier="lab", rng=rng)
            A = g.preprocess.absorbance(Ri)
            var, sc = g.lab.pca_scaled(A)
            pc1[add].append(var[0])
            lvl = d[f"{add}_pct"].to_numpy()
            rho = spearmanr(lvl, sc[:, 0])[0]
            (t2 if add == "seacoal" else t3).append(rho)
            auc = g.lab.relative_auc(A, ins.centers, d["clay_pct"].to_numpy(), lvl)
            d = d.assign(additive=add, AUC=auc)
            tab.append(d)
            mono = all(np.all(np.diff(d[d.clay_pct == dc].sort_values(f"{add}_pct").AUC) > 0) for dc in g.lab.DC2_LEVELS)
            t4.append(mono)
        tab = pd.concat(tab)
        t5.append(tab[tab.additive == "seacoal"].AUC.max() > tab[tab.additive == "iron_oxide"].AUC.max())
        aucs.append(tab[(tab.seacoal_pct > 0) | (tab.iron_oxide_pct > 0)].AUC.to_numpy())
    return pc1, np.array(t2), np.array(t3), np.array(t4), np.array(t5), np.array(aucs)


def main():
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    cal = json.load(open(os.path.join(PROC, "lab_calibration.json")))
    lab = pd.read_csv(os.path.join(ROOT, rules["lab_calibration"]["data"]))
    lab = lab[lab.additive_pct > 0].reset_index(drop=True)
    lab_auc = lab.AUC.to_numpy()
    dc = lab.dc2_pct.to_numpy()
    offsets = np.array([cal["group_offsets"][str(int(k))] for k in dc])

    E = g.io.load_endmembers(rules, RAW)
    ins = g.instrument.Instrument(rules, E.wl)
    cal_grains = {**{k: v for k, v in E.grain_um.items() if not isinstance(v, str)},
                  "seacoal": cal["seacoal_um"], "iron_oxide": cal["iron_oxide_um"]}
    prior_grains = {**cal_grains, "seacoal": rules["components"]["seacoal"]["grain_um_fallback"],
                    "iron_oxide": rules["components"]["iron_oxide"]["grain_um_fallback"]}
    variants = {
        "calibrated default (Hapke, lab-fitted sizes)": (E, cal_grains, rules["mixing_model"]),
        "USGS priors only (Hapke, seacoal 75 um, iron oxide 5 um)": (E, prior_grains, rules["mixing_model"]),
        "linear mixing (same spectra)": (E, cal_grains, "linear"),
    }
    rows, comp = [], lab[["sample_id", "additive", "dc2_pct", "additive_pct", "AUC"]].copy()
    rng = np.random.default_rng(2025)
    for name, (Ev, grains, model) in variants.items():
        pc1, t2, t3, t4, t5, aucs = run_variant(Ev, ins, grains, model, rng)
        mean_auc = aucs.mean(axis=0)
        r_auc = float(np.corrcoef(mean_auc, lab_auc)[0, 1])
        rmse_raw = float(np.sqrt(np.mean((mean_auc - lab_auc) ** 2)))
        rmse_off = float(np.sqrt(np.mean((mean_auc + offsets - lab_auc) ** 2)))
        checks = {
            "T1": bool(np.median(pc1["seacoal"]) > 95 and np.median(pc1["iron_oxide"]) > 95),
            "T2": bool(np.median(t2) > 0.8), "T3": bool(np.median(t3) > 0.8),
            "T4": bool(np.mean(t4) >= 0.95), "T5": bool(np.mean(t5) >= 0.95),
        }
        rows.append({"variant": name,
                     "PC1_seacoal_median_pct": round(float(np.median(pc1["seacoal"])), 2),
                     "PC1_iron_oxide_median_pct": round(float(np.median(pc1["iron_oxide"])), 2),
                     "rho_PC1_seacoal": round(float(np.median(t2)), 3),
                     "rho_PC1_iron_oxide": round(float(np.median(t3)), 3),
                     "AUC_monotone_share": round(float(np.mean(t4)), 3),
                     "AUC_vs_lab_r": round(r_auc, 3), "AUC_rmse_vs_lab": round(rmse_raw, 1),
                     "AUC_rmse_vs_lab_with_group_offsets": round(rmse_off, 1),
                     **{k: "PASS" if v else "FAIL" for k, v in checks.items()},
                     "trends_reproduced": f"{sum(checks.values())}/5"})
        comp[f"model_AUC__{name.split(' (')[0].replace(' ', '_')}"] = mean_auc.round(1)
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(PROC, "lab_trends.csv"), index=False)
    comp.to_csv(os.path.join(PROC, "lab_auc_comparison.csv"), index=False)
    pd.set_option("display.width", 250)
    print(df.T.to_string())
    stats = json.load(open(STATS))
    stats["lab_trends"] = {"lab_pc1": LAB_PC1, "n_repeats": N_REPEATS, "tier": "lab", "results": rows}
    json.dump(stats, open(STATS, "w"), indent=2)


if __name__ == "__main__":
    main()
