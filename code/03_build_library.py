#!/usr/bin/env python3
"""Step 3: compute the spectral library (dry v1.0) and the moisture extension, with quality checks.

Plain-language summary: this script reads the mixing rules you set in
config/mixing_rules.json, computes a spectrum for every recipe in the grid,
saves the library files, and writes a quality report
(data/processed/qa_report.txt) plus the numbers used in documents
(paper/stats.json). You do not need to open this file; run it and read the QA report.

Outputs
  library/v1.0/      dry library: compositions, native 1 nm spectra, instrument-resolution spectra
  library/moisture/  moisture extension
  library/endmembers_native1nm.csv   the reference spectra actually used
  data/processed/qa_report.txt, data/processed/hematite_fit.csv
  paper/stats.json   (library section)
"""

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402
from greensand_nir.compositions import ORDER  # noqa: E402

RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
PROC = os.path.join(ROOT, "data", "processed")
LIB = os.path.join(ROOT, "library")
STATS = os.path.join(ROOT, "paper", "stats.json")


def mixing_model_check(rules, E):
    """Independent check: Hapke vs linear mixing on the measured USGS 2% hematite + 98% quartz mixture (GDS76).

    The hematite size is fitted only for this check (GDS76 used fine quartz and its own hematite);
    it is not used in the library."""
    f = rules["mixing_model_check"]
    wl = E.wl
    mixm = E.extra[f["mixture_spectrum"]]
    q = E.extra[f["quartz_spectrum"]]
    hem = E.extra[f["hematite_spectrum"]]
    lw = (wl >= 1600) & (wl <= 2300)
    scale = float(np.mean(mixm[lw] / q[lw]))
    qs = q * scale  # GDS76 quartz is brighter than GDS31; match its long-wavelength level
    fh = f["hematite_mass_fraction"]
    rho_h, rho_q = E.density["iron_oxide"], E.density["silica_sand"]  # hematite and quartz densities from the rules
    best, rmse, (grid, errs) = g.mixing.fit_grain_ratio(
        mixm, hem, qs, fh, rho_h, rho_q, f["quartz_grain_um"], wl=wl, band=tuple(rules["native_range_nm"]))
    pred_h = g.mixing.mix(np.vstack([hem, qs]), [fh, 1 - fh], [rho_h, rho_q], [best, f["quartz_grain_um"]])
    pred_l = g.mixing.mix(np.vstack([hem, qs]), [fh, 1 - fh], model="linear")
    pd.DataFrame({"wavelength_nm": wl, "measured_GDS76": mixm, "quartz_scaled": qs,
                  "hapke_fit": pred_h, "linear": pred_l}).to_csv(
        os.path.join(PROC, "hematite_fit.csv"), index=False, float_format="%.5f")
    pd.DataFrame({"hematite_grain_um": grid, "rmse": errs}).to_csv(
        os.path.join(PROC, "hematite_fit_curve.csv"), index=False, float_format="%.6f")
    i1000 = int(np.argmin(abs(wl - 1000)))
    return {
        "hematite_grain_um": round(best, 2),
        "hematite_to_quartz_size_ratio": round(best / f["quartz_grain_um"], 3),
        "quartz_scale": round(scale, 3),
        "rmse_hapke": round(rmse, 4),
        "rmse_linear": round(float(np.sqrt(np.mean((pred_l - mixm) ** 2))), 4),
        "R1000_measured": round(float(mixm[i1000]), 3),
        "R1000_hapke": round(float(pred_h[i1000]), 3),
        "R1000_linear": round(float(pred_l[i1000]), 3),
    }


def compute(E, rules, comps, model=None, path_factor=None):
    order = list(ORDER)
    M = E.matrix(order)
    d = [E.density[o] for o in order]
    gr = [E.grain_um[o] for o in order]
    m = g.compositions.mass_fractions(comps, order)
    moist = comps["moisture_pct"].to_numpy()
    return g.mixing.mix(M, m, d, gr, model=model or rules["mixing_model"],
                        moisture_pct=moist if moist.max() > 0 else None,
                        water_alpha=E.water_alpha,
                        path_factor=path_factor if path_factor is not None else rules["water"]["path_factor"])


def save_set(folder, stem, comps, R_native, wl, ins):
    os.makedirs(folder, exist_ok=True)
    ids = [f"{stem}-{i:05d}" for i in range(len(comps))]
    c = comps.copy()
    c.insert(0, "sample_id", ids)
    c.to_csv(os.path.join(folder, f"{stem}_compositions.csv"), index=False, float_format="%.4f")
    nat = pd.DataFrame(R_native, columns=[f"R_{int(w)}" for w in wl])
    nat.insert(0, "sample_id", ids)
    nat.to_csv(os.path.join(folder, f"{stem}_spectra_native1nm.csv.gz"), index=False,
               float_format="%.5f", compression={"method": "gzip", "mtime": 0})
    Ri = ins.resample(R_native)
    # channel centres are not whole numbers (6.93 nm spacing): label them to 0.01 nm, as in the benchmark sets
    inst = pd.DataFrame(Ri, columns=[f"R_{w:.2f}" for w in ins.centers])
    inst.insert(0, "sample_id", ids)
    inst.to_csv(os.path.join(folder, f"{stem}_spectra_instrument.csv"), index=False, float_format="%.5f")
    return Ri


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules", default=os.path.join(ROOT, "config", "mixing_rules.json"))
    a = ap.parse_args()
    os.makedirs(PROC, exist_ok=True)
    rules = g.io.load_rules(a.rules)
    E = g.io.load_endmembers(rules, RAW)
    wl = E.wl
    qa = ["GREEN SAND NIR REFERENCE LIBRARY: QA REPORT",
          "Plain-language summary: counts, range checks, physical-direction checks and the",
          "model check against a measured USGS mixture. Every PASS/FAIL below is computed.", ""]

    # 1. effective sizes calibrated to the lab (step 2), and the independent mixing-model check
    cal_path = os.path.join(PROC, "lab_calibration.json")
    cal = json.load(open(cal_path)) if os.path.exists(cal_path) else {}
    for comp in ("seacoal", "iron_oxide"):
        if E.grain_um[comp] == "lab_fit":
            if f"{comp}_um" in cal and cal.get(f"{comp}_spectrum") == E.files[comp]:
                E.grain_um[comp] = float(cal[f"{comp}_um"])
            else:
                E.grain_um[comp] = float(rules["components"][comp]["grain_um_fallback"])
                print(f"WARNING: no matching lab calibration for {comp}; using fallback size")
    hf = mixing_model_check(rules, E)
    qa += ["[0] Effective grain sizes used (um): " + ", ".join(f"{k} {E.grain_um[k]}" for k in ORDER),
           f"    seacoal and iron oxide sizes calibrated to {cal.get('n_lab_values', 0)} measured lab AUC values "
           f"(RMSE {cal.get('rmse_with_offsets')} AUC units; lab AUC range {cal.get('lab_auc_range')})", "",
           "[1] Mixing model check: USGS measured 2% hematite + 98% quartz (GDS76), hematite GDS27",
           f"    hematite size fitted for this check only: {hf['hematite_grain_um']} um "
           f"(ratio to quartz {hf['hematite_to_quartz_size_ratio']})",
           f"    RMSE 1000-2350 nm: Hapke {hf['rmse_hapke']}  vs linear {hf['rmse_linear']}",
           f"    reflectance at 1000 nm: measured {hf['R1000_measured']}, Hapke {hf['R1000_hapke']}, "
           f"linear {hf['R1000_linear']}",
           f"    {'PASS' if hf['rmse_hapke'] < hf['rmse_linear'] else 'FAIL'}: Hapke closer to measurement than linear", ""]

    # 2. endmember table
    em = pd.DataFrame({"wavelength_nm": wl, **{k: E.spectra[k] for k in ORDER}})
    wl_all = g.io.read_wavelengths_nm(os.path.join(RAW, rules["wavelength_file"]))
    keep = (wl_all >= wl[0] - 0.01) & (wl_all <= wl[-1] + 0.01)
    for comp, cfg in rules["components"].items():
        for alt, fname in cfg.get("alternatives", {}).items():
            em[f"{comp}__alt_{alt}"] = g.io.read_splib(os.path.join(RAW, fname))[keep]
    os.makedirs(LIB, exist_ok=True)
    em.to_csv(os.path.join(LIB, "endmembers_native1nm.csv"), index=False, float_format="%.6f")
    xs = g.mixing.cross_section_fractions(np.array([0.885, 0.08, 0.03, 0.005]),
                                          [E.density[o] for o in ORDER], [E.grain_um[o] for o in ORDER])

    ins = g.instrument.Instrument(rules, wl)

    # 3. dry library
    dry = g.compositions.grid(rules["library_grid"])
    Rd = compute(E, rules, dry)
    Rdi = save_set(os.path.join(LIB, "v1.0"), "GSNIR-v1.0", dry, Rd, wl, ins)

    # 4. moisture extension
    wet = g.compositions.grid(rules["moisture_grid"])
    Rw = compute(E, rules, wet)
    Rwi = save_set(os.path.join(LIB, "moisture"), "GSNIR-moist-v1.0", wet, Rw, wl, ins)

    # 5. QA checks
    def rng_check(R, name):
        ok = np.isfinite(R).all() and R.min() > 0 and R.max() < 1
        return f"    {'PASS' if ok else 'FAIL'}: {name} all reflectance finite and within (0,1): min {R.min():.4f}, max {R.max():.4f}"

    def mono(R, comps, col, other_cols, band=None):
        """Share of neighbour pairs (same other columns, next level up in col) where mean reflectance
        (over `band` nm, default the full range) falls."""
        df = comps.copy()
        sel = np.ones(len(wl), bool) if band is None else (wl >= band[0]) & (wl <= band[1])
        df["mR"] = R[:, sel].mean(axis=1)
        df = df.sort_values(other_cols + [col])
        dif = df.groupby(other_cols)["mR"].diff().dropna()
        return float((dif < 0).mean()), len(dif)

    qa += ["[2] Row counts",
           f"    dry library v1.0: {len(dry)} recipes x {len(wl)} native channels; "
           f"{Rdi.shape[1]} instrument channels",
           f"    moisture extension: {len(wet)} recipes x {len(wl)} native channels", "",
           "[3] Range checks", rng_check(Rd, "dry library"), rng_check(Rw, "moisture extension"), ""]
    sc_share, sc_n = mono(Rd, dry, "seacoal_pct", ["clay_pct", "iron_oxide_pct"])
    fe_share, fe_n = mono(Rd, dry, "iron_oxide_pct", ["clay_pct", "seacoal_pct"], band=(1000, 1020))
    fe_full, _ = mono(Rd, dry, "iron_oxide_pct", ["clay_pct", "seacoal_pct"])
    mw_share, mw_n = mono(Rw, wet, "moisture_pct", ["clay_pct", "seacoal_pct", "iron_oxide_pct"])
    i1940 = int(np.argmin(abs(wl - 1940)))
    qa += ["[4] Physical-direction checks (more absorber should darken the sample)",
           f"    {'PASS' if sc_share == 1 else 'FAIL'}: more seacoal lowers mean reflectance in {sc_share:.1%} of {sc_n} steps",
           f"    {'PASS' if fe_share == 1 else 'FAIL'}: more iron oxide lowers 1000-1020 nm reflectance (Fe3+ band edge) in {fe_share:.1%} of {fe_n} steps",
           f"    NOTE: over the full 1000-2350 nm range, more iron oxide lowers mean reflectance in {fe_full:.1%} of steps",
           f"          (not 100%: in the darkest, high-seacoal recipes the mixture is already darker than the iron oxide itself, so adding it lightens the average)",
           f"    {'PASS' if mw_share == 1 else 'FAIL'}: more moisture lowers mean reflectance in {mw_share:.1%} of {mw_n} steps", ""]
    # water band depth at a reference recipe
    ref = wet[(wet.clay_pct == 8) & (wet.seacoal_pct == 3) & (wet.iron_oxide_pct == 0.5)]
    refd = dry[(dry.clay_pct == 8) & (dry.seacoal_pct == 3) & (dry.iron_oxide_pct == 0.5)]
    r1940_dry = float(Rd[refd.index[0], i1940])
    water_rows = [(float(m), float(Rw[i, i1940])) for i, m in zip(ref.index, ref.moisture_pct)]
    qa += ["[5] Water band at 1940 nm, reference recipe 8% clay, 3% seacoal, 0.5% iron oxide",
           f"    dry: R1940 = {r1940_dry:.4f}"] + [f"    moisture {m:.1f}%: R1940 = {r:.4f}" for m, r in water_rows] + [""]

    # spot rows for the verification checklist
    spots = [(3, 0, 0), (12, 0, 0), (8, 3, 0.5), (8, 5, 2), (3, 5, 2)]
    i1700 = int(np.argmin(abs(wl - 1700)))
    qa.append("[6] Spot rows (dry library, native 1 nm; columns R_1100, R_1700, R_2200)")
    spot_out = []
    for c, s, f in spots:
        row = dry[(dry.clay_pct == c) & (dry.seacoal_pct == s) & (np.isclose(dry.iron_oxide_pct, f))].index[0]
        vals = [float(Rd[row, int(np.argmin(abs(wl - x)))]) for x in (1100, 1700, 2200)]
        sid = f"GSNIR-v1.0-{row:05d}"
        qa.append(f"    {sid}: clay {c}%, seacoal {s}%, iron oxide {f}% -> " + ", ".join(f"{v:.5f}" for v in vals))
        spot_out.append({"sample_id": sid, "clay": c, "seacoal": s, "iron_oxide": f,
                         "R1100": round(vals[0], 5), "R1700": round(vals[1], 5), "R2200": round(vals[2], 5)})
    qa += ["", "[7] Endmember values at 1700 nm (check against the USGS source files)"]
    for k in ORDER:
        qa.append(f"    {k}: {E.files[k]} -> {E.spectra[k][i1700]:.5f}")
    qa += ["", f"[8] Cross-section shares for 88.5/8/3/0.5 sand/clay/seacoal/iron oxide: "
           + ", ".join(f"{k} {v:.3f}" for k, v in zip(ORDER, xs))]
    with open(os.path.join(PROC, "qa_report.txt"), "w") as fh:
        fh.write("\n".join(qa) + "\n")
    print("\n".join(qa))

    stats = json.load(open(STATS)) if os.path.exists(STATS) else {}
    stats["library"] = {
        "n_dry": int(len(dry)), "n_moist": int(len(wet)), "n_native_channels": int(len(wl)),
        "n_instrument_channels": int(Rdi.shape[1]), "mixing_model_check": hf,
        "grain_um": {k: E.grain_um[k] for k in ORDER}, "density": {k: E.density[k] for k in ORDER},
        "endmember_files": E.files, "seacoal_monotone_share": sc_share, "iron_oxide_monotone_share_1000_1020": fe_share, "iron_oxide_monotone_share_full": fe_full,
        "moisture_monotone_share": mw_share, "R1940_ref_dry": round(r1940_dry, 4),
        "R1940_ref_wet": {f"{m:.1f}": round(r, 4) for m, r in water_rows},
        "cross_section_shares_ref": {k: round(float(v), 3) for k, v in zip(ORDER, xs)},
        "spot_rows": spot_out,
        "endmember_R1700": {k: round(float(E.spectra[k][i1700]), 5) for k in ORDER},
        "rules_version": rules["version"], "mixing_model": rules["mixing_model"],
    }
    os.makedirs(os.path.dirname(STATS), exist_ok=True)
    json.dump(stats, open(STATS, "w"), indent=2)


if __name__ == "__main__":
    main()
