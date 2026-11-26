#!/usr/bin/env python3
"""Step 9: figures, tables and number macros for the preprint (paper/preprint/).

Plain-language summary: draws every preprint figure (vector PDF, Matplotlib),
writes every table as LaTeX, and writes macros.tex, which holds every number the
preprint text quotes. The preprint (paper/preprint/main.tex) reads these files,
so the text cannot drift from the data. Run after steps 1-5.
"""

import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402
from greensand_nir.compositions import ORDER  # noqa: E402

OUT = os.path.join(ROOT, "paper", "preprint")
FIG = os.path.join(OUT, "figures")
TAB = os.path.join(OUT, "tables")
RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
PROC = os.path.join(ROOT, "data", "processed")
os.makedirs(FIG, exist_ok=True)
os.makedirs(TAB, exist_ok=True)

S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
CAL = S["lab_calibration"]

# Validated categorical palette (dataviz reference, light mode) and one-hue sequential ramp
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#104281", "#0d366b"]
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8, "axes.labelsize": 8.5, "axes.titlesize": 8.5,
    "xtick.labelsize": 7.5, "ytick.labelsize": 7.5, "legend.fontsize": 7, "axes.linewidth": 0.8,
    "axes.edgecolor": "#222222", "axes.grid": True, "grid.color": "#e3e3e3", "grid.linewidth": 0.5,
    "axes.axisbelow": True, "xtick.direction": "in", "ytick.direction": "in", "xtick.top": True,
    "ytick.right": True, "xtick.major.size": 3, "ytick.major.size": 3, "lines.linewidth": 1.3,
    "legend.frameon": True, "legend.framealpha": 0.92, "legend.edgecolor": "#cccccc",
    "savefig.bbox": "tight", "savefig.pad_inches": 0.02, "pdf.fonttype": 42,
})
W1, W2 = 3.4, 7.0
NAMES = {"silica_sand": "Silica sand", "clay": "Bentonite", "seacoal": "Seacoal", "iron_oxide": "Iron oxide"}

macros = {}


def M(name, value):
    macros[name] = value


def save(fig, name):
    fig.savefig(os.path.join(FIG, name + ".pdf"))
    fig.savefig(os.path.join(FIG, name + ".png"), dpi=220)
    plt.close(fig)


def panel(ax, letter):
    ax.text(0.02, 0.97, f"({letter})", transform=ax.transAxes, va="top", ha="left", fontsize=8.5, weight="bold")


def f(x, d=2):
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "n.r."
    return f"{x:.{d}f}"


def g_(x):
    return "n.r." if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:g}"


# ------------------------------------------------------------------ endmembers
E = g.io.load_endmembers(rules, RAW)
E.grain_um["seacoal"], E.grain_um["iron_oxide"] = CAL["seacoal_um"], CAL["iron_oxide_um"]
wl = E.wl
ins = g.instrument.Instrument(rules, wl)

fig, axes = plt.subplots(2, 1, figsize=(W1, 4.1), gridspec_kw={"height_ratios": [2.2, 1]}, sharex=True)
ax = axes[0]
for i, k in enumerate(["silica_sand", "clay", "iron_oxide", "seacoal"]):
    ax.plot(wl, E.spectra[k], color=C[i], label=f"{NAMES[k]} ({E.files[k].split('s07_ASD_')[1].split('_BECK')[0].split('_ASD')[0].replace('_', ' ')})")
em = pd.read_csv(os.path.join(ROOT, "library", "endmembers_native1nm.csv"))
ax.plot(wl, em["iron_oxide__alt_hematite_GDS27_bright"], color="#8a8984", ls="--", lw=0.9, label="Hematite GDS27 (rejected)")
ax.plot(wl, em["seacoal__alt_carbon_black"], color="#8a8984", ls=":", lw=1.0, label="Carbon black GDS68 (alternative)")
for x in (1414, 1910, 2206):
    ax.axvline(x, color="#bbbbbb", lw=0.6, ls="-", zorder=0)
ax.set_ylabel("Reflectance")
ax.set_ylim(0, 0.92)
panel(ax, "a")
ax = axes[1]
ax.semilogy(wl, E.water_alpha * 1e4, color=C[0])
ax.set_ylabel(r"$\alpha_{\rm w}$ (cm$^{-1}$)")
ax.set_xlabel("Wavelength (nm)")
ax.set_xlim(1000, 2350)
panel(ax, "b")
fig.tight_layout(h_pad=0.4)
h_, l__ = axes[0].get_legend_handles_labels()
fig.legend(h_, l__, loc="upper center", bbox_to_anchor=(0.55, 0.0), ncol=2, fontsize=6, frameon=False)
save(fig, "fig1_endmembers")
i1450, i1940 = int(np.argmin(abs(wl - 1450))), int(np.argmin(abs(wl - 1940)))
M("alphaFourteen", f"{E.water_alpha[i1450] * 1e4:.0f}")
M("alphaNineteen", f"{E.water_alpha[i1940] * 1e4:.0f}")

# ------------------------------------------------------------------ GDS76 mixing check
hf = pd.read_csv(os.path.join(PROC, "hematite_fit.csv"))
fig, ax = plt.subplots(figsize=(W1, 2.4))
ax.plot(hf.wavelength_nm, hf.measured_GDS76, color="#222222", lw=1.6, label="Measured (USGS GDS76)")
ax.plot(hf.wavelength_nm, hf.hapke_fit, color=C[0], label="Hapke (albedo) mixing")
ax.plot(hf.wavelength_nm, hf.linear, color=C[1], ls="--", label="Linear (reflectance) mixing")
ax.plot(hf.wavelength_nm, hf.quartz_scaled, color="#8a8984", lw=0.9, ls=":", label="Quartz end-member (scaled)")
ax.set(xlabel="Wavelength (nm)", ylabel="Reflectance", xlim=(1000, 2350), ylim=(0.7, 0.96))
ax.legend(loc="lower right")
save(fig, "fig2_gds76")
mm = S["library"]["mixing_model_check"]
r0 = hf.iloc[0]
M("dropMeas", f"{r0.quartz_scaled - r0.measured_GDS76:.3f}")
M("dropLin", f"{r0.quartz_scaled - r0.linear:.3f}")
M("dropHapke", f"{r0.quartz_scaled - r0.hapke_fit:.3f}")
M("dropRatio", f"{(r0.quartz_scaled - r0.measured_GDS76) / (r0.quartz_scaled - r0.linear):.0f}")
for k, v in mm.items():
    M("mm" + "".join(p.capitalize() for p in k.replace("1000", "Thousand").split("_")), v)

# ------------------------------------------------------------------ calibration surface and fits
lab = pd.read_csv(os.path.join(ROOT, rules["lab_calibration"]["data"]))
labp = lab[lab.additive_pct > 0].reset_index(drop=True)
labp["add"] = labp.additive.map({"Seacoal": "seacoal", "Red Iron Oxide": "iron_oxide"})
y = labp.AUC.to_numpy()
dc = labp.dc2_pct.to_numpy()
is_sc = (labp["add"] == "seacoal").to_numpy()
grid = np.geomspace(1, 300, 45)


def curves(add):
    out = []
    for d in grid:
        gr = dict(E.grain_um)
        gr[add] = d
        tab = g.lab.lab_auc_table(E, ins, gr)
        out.append(tab[tab.additive == add].AUC.to_numpy())
    return np.array(out)


csc, cfe = curves("seacoal"), curves("iron_oxide")
Z = np.zeros((len(grid), len(grid)))
for i in range(len(grid)):
    for j in range(len(grid)):
        pred = np.where(is_sc, 0.0, 0.0)
        pred[is_sc] = csc[i]
        pred[~is_sc] = cfe[j]
        r = y - pred
        off = {k: r[dc == k].mean() for k in np.unique(dc)}
        Z[i, j] = np.sqrt(np.mean((r - np.array([off[k] for k in dc])) ** 2))
fit = pd.read_csv(os.path.join(PROC, "lab_calibration_fit.csv"))
fig, axes = plt.subplots(1, 3, figsize=(W2, 2.45), gridspec_kw={"width_ratios": [1.15, 1, 1]})
ax = axes[0]
cs = ax.contourf(grid, grid, Z, levels=np.linspace(Z.min(), min(Z.max(), 160), 14), cmap="Blues_r")
ax.contour(grid, grid, Z, levels=[Z.min() * 1.25], colors="#222222", linewidths=0.8, linestyles="--")
ax.set_xscale("log")
ax.set_yscale("log")
ax.plot(CAL["iron_oxide_um"], CAL["seacoal_um"], marker="*", ms=10, color=C[1], mec="white", mew=0.8, ls="none",
        label="Best fit")
for k, row in enumerate(CAL["leave_one_group_out"]):
    ax.plot(row["iron_oxide_um"], row["seacoal_um"], marker="o", ms=4, color=C[3], mec="#222222", mew=0.5, ls="none",
            label="Leave-one-DC2-out" if k == 0 else None)
ax.set(xlabel=r"Iron oxide effective size $d_{\rm Fe}$ ($\mu$m)", ylabel=r"Seacoal effective size $d_{\rm sc}$ ($\mu$m)")
ax.legend(loc="upper right", fontsize=6)
cb = fig.colorbar(cs, ax=ax, pad=0.02)
cb.set_label("RMSE (AUC units)", fontsize=7)
cb.ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f"))
cb.ax.tick_params(labelsize=6.5)
ax.grid(False)
panel(ax, "a")
for ax, col, title, letter in ((axes[1], "model_AUC", "Computed AUC", "b"),
                               (axes[2], "model_plus_offset", "Computed AUC + group offset", "c")):
    for i, (add, lab_) in enumerate((("seacoal", "Seacoal"), ("iron_oxide", "Red iron oxide"))):
        d = fit[fit["add"] == add]
        ax.scatter(d[col], d.AUC, s=18, color=C[i], edgecolor="white", linewidth=0.6, label=lab_, zorder=3)
    ax.plot([0, 600], [0, 600], color="#555555", lw=0.8, ls="--")
    r = np.sqrt(np.mean((fit[col] - fit.AUC) ** 2))
    ax.set(xlim=(0, 600), ylim=(0, 600), xlabel=title + r" (A$\cdot$nm)")
    ax.text(0.97, 0.05, f"RMSE = {r:.0f}", transform=ax.transAxes, ha="right", fontsize=7)
    panel(ax, letter)
axes[1].set_ylabel(r"Measured AUC (A$\cdot$nm)")
axes[1].legend(loc="upper left", bbox_to_anchor=(0.0, 0.9), fontsize=6.5)
fig.tight_layout(w_pad=0.6)
save(fig, "fig3_calibration")
M("rmseRaw", f"{np.sqrt(np.mean((fit.model_AUC - fit.AUC) ** 2)):.0f}")
M("rmseOff", f"{CAL['rmse_with_offsets']:.1f}")
M("rmseOffOnly", f"{CAL['rmse_offsets_only_no_additive_model']:.1f}")
M("labAucSd", f"{CAL['lab_auc_sd']:.1f}")
M("labAucMin", f"{CAL['lab_auc_range'][0]:.0f}")
M("labAucMax", f"{CAL['lab_auc_range'][1]:.0f}")
M("dSc", f"{CAL['seacoal_um']:.1f}")
M("dFe", f"{CAL['iron_oxide_um']:.2f}")
loo = CAL["leave_one_group_out"]
M("dScLo", f"{min(r['seacoal_um'] for r in loo):.1f}")
M("dScHi", f"{max(r['seacoal_um'] for r in loo):.1f}")
M("dFeLo", f"{min(r['iron_oxide_um'] for r in loo):.2f}")
M("dFeHi", f"{max(r['iron_oxide_um'] for r in loo):.2f}")
for k, v in CAL["group_offsets"].items():
    M("off" + {"3": "Three", "6": "Six", "9": "Nine", "12": "Twelve"}[k], f"{v:.0f}")
resid = fit.residual.to_numpy()
M("residMaxAbs", f"{np.max(np.abs(resid)):.0f}")
r_sc = np.corrcoef(fit[fit['add'] == 'seacoal'].model_plus_offset, fit[fit['add'] == 'seacoal'].AUC)[0, 1]
r_fe = np.corrcoef(fit[fit['add'] == 'iron_oxide'].model_plus_offset, fit[fit['add'] == 'iron_oxide'].AUC)[0, 1]
M("rFitSc", f"{r_sc:.2f}")
M("rFitFe", f"{r_fe:.2f}")
# implied mean absorbance shift of the offsets
M("offAbsLo", f"{min(CAL['group_offsets'].values()) / 1350:.3f}")
M("offAbsHi", f"{max(CAL['group_offsets'].values()) / 1350:.3f}")

# ------------------------------------------------------------------ PC1 replication figure
rng = np.random.default_rng(11)
fig, axes = plt.subplots(1, 2, figsize=(W2, 2.5))
pcvals = {}
for ax, add, title, letter in ((axes[0], "seacoal", "Seacoal series", "a"), (axes[1], "iron_oxide", "Red iron oxide series", "b")):
    reps = []
    for _ in range(50):
        d, Ri = g.lab.simulate(E, ins, add, E.grain_um, tier="lab", rng=rng)
        var, sc = g.lab.pca_scaled(g.preprocess.absorbance(Ri))
        reps.append(sc[:, 0])
        pcvals.setdefault(add, []).append(var[0])
    sc_mean = np.mean(reps, axis=0)
    for k, dcl in enumerate(g.lab.DC2_LEVELS):
        sel = (d.clay_pct == dcl).to_numpy()
        col_k = SEQ[[2, 4, 6, 7][k]]
        ax.plot(d[f"{add}_pct"][sel], sc_mean[sel], color=col_k, lw=1.2, label=f"Computed, DC2 {dcl}%")
        tab = lab.iloc[16:32] if add == "iron_oxide" else lab.iloc[0:16]
        tab = tab[tab.dc2_pct == dcl]
        ax.plot(tab.additive_pct, tab.PC1, ls="none", marker="o", ms=4, color=col_k, mec="#222222", mew=0.5,
                label=f"Measured, DC2 {dcl}%")
    ax.set(xlabel=("Seacoal" if add == "seacoal" else "Red iron oxide") + " (% of dry mix)", ylabel="PC1 score")
    ax.set_title(title, fontsize=8)
    ax.text(0.03, 0.80, f"PC1 variance: {np.median(pcvals[add]):.1f}% computed,\n"
            f"{99.23 if add == 'seacoal' else 97.87}% measured", transform=ax.transAxes, fontsize=6.5, va="top")
    panel(ax, letter)
h, l_ = axes[1].get_legend_handles_labels()
axes[1].legend(h, l_, loc="lower right", fontsize=5.6, ncol=2)
fig.tight_layout(w_pad=1.0)
save(fig, "fig4_pc1")

# ------------------------------------------------------------------ library examples
comp = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_compositions.csv"))
spec = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_spectra_native1nm.csv.gz"))
SPEC = spec.iloc[:, 1:].to_numpy(float)
fig, axes = plt.subplots(1, 3, figsize=(W2, 2.4), sharey=True)
series = [("seacoal_pct", [0, 1, 2, 3, 4, 5], dict(clay_pct=8, iron_oxide_pct=0), "Seacoal (8% clay)", "a"),
          ("iron_oxide_pct", [0, 0.4, 0.8, 1.2, 1.6, 2.0], dict(clay_pct=8, seacoal_pct=0), "Iron oxide (8% clay)", "b"),
          ("clay_pct", [3, 5, 7, 9, 11, 12], dict(seacoal_pct=0, iron_oxide_pct=0), "Bentonite (no additive)", "c")]
for ax, (col, levels, fixed, title, letter) in zip(axes, series):
    for i, L in enumerate(levels):
        sel = np.isclose(comp[col].to_numpy(), L)
        for k, v in fixed.items():
            sel &= np.isclose(comp[k].to_numpy(), v)
        ax.plot(wl, SPEC[sel][0], color=SEQ[i + 2], lw=1.1, label=f"{L:g}%")
    ax.set(xlabel="Wavelength (nm)", xlim=(1000, 2350))
    ax.set_title(title, fontsize=8)
    ax.legend(loc="lower left", fontsize=5.8, ncol=2, title=None)
    panel(ax, letter)
axes[0].set_ylabel("Computed reflectance")
fig.tight_layout(w_pad=0.5)
save(fig, "fig5_library")

# ------------------------------------------------------------------ moisture
wcomp = pd.read_csv(os.path.join(ROOT, "library", "moisture", "GSNIR-moist-v1.0_compositions.csv"))
wspec = pd.read_csv(os.path.join(ROOT, "library", "moisture", "GSNIR-moist-v1.0_spectra_native1nm.csv.gz")).iloc[:, 1:].to_numpy(float)
fig, ax = plt.subplots(figsize=(W1, 2.5))
sel = (comp.clay_pct == 8) & np.isclose(comp.seacoal_pct, 3) & np.isclose(comp.iron_oxide_pct, 0.5)
ax.plot(wl, SPEC[sel.to_numpy()][0], color="#222222", lw=1.4, label="Dry")
for i, mw in enumerate([2.0, 3.0, 4.0, 5.0]):
    s2 = (wcomp.clay_pct == 8) & np.isclose(wcomp.seacoal_pct, 3) & np.isclose(wcomp.iron_oxide_pct, 0.5) & np.isclose(wcomp.moisture_pct, mw)
    ax.plot(wl, wspec[s2.to_numpy()][0], color=SEQ[2 + i * 2 if i < 3 else 7], lw=1.1, label=f"{mw:g}% water")
ax.set(xlabel="Wavelength (nm)", ylabel="Computed reflectance", xlim=(1000, 2350))
ax.legend(loc="lower left", fontsize=6.5)
save(fig, "fig6_moisture")
m_ref = np.array([[0.885, 0.08, 0.03, 0.005]])
t35 = g.mixing.film_thickness_um(m_ref, [E.density[o] for o in ORDER], [E.grain_um[o] for o in ORDER], 3.5)[0]
M("filmThreeFive", f"{t35:.2f}")
M("RnineteenDry", f"{S['library']['R1940_ref_dry']:.3f}")
M("RnineteenWetTwo", f"{S['library']['R1940_ref_wet']['2.0']:.3f}")
M("RnineteenWetFive", f"{S['library']['R1940_ref_wet']['5.0']:.3f}")

# ------------------------------------------------------------------ power curves
pc = pd.read_csv(os.path.join(ROOT, "benchmark", "power_curves.csv"))
methods = ["PLSR", "PCA-LDA", "SVM-RBF", "RandomForest", "GradientBoosting"]
fig, axes = plt.subplots(1, 2, figsize=(W2, 2.5), sharey=True)
for ax, tgt, title, letter in ((axes[0], "seacoal", "Seacoal, dry sand, lab noise", "a"),
                               (axes[1], "iron_oxide", "Red iron oxide, dry sand, lab noise", "b")):
    for i, m in enumerate(methods):
        d = pc[(pc.track == "dry") & (pc.tier == "lab") & (pc.target == tgt) & (pc.method == m)]
        ax.plot(d.level, d.power, marker="o", ms=3, color=C[i], label=m)
    ax.axhline(0.95, color="#555555", lw=0.8, ls=":")
    ax.set_xscale("log")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
    ax.set(xlabel="Additive level (% of dry mix)", ylim=(-0.03, 1.05))
    ax.set_title(title, fontsize=8)
    panel(ax, letter)
axes[0].set_ylabel(r"Detection power (false alarms $=5\%$)")
axes[1].legend(loc="lower right", fontsize=6.3)
fig.tight_layout(w_pad=0.6)
save(fig, "fig7_power")

# ------------------------------------------------------------------ LOD heatmap
lb = pd.read_csv(os.path.join(ROOT, "benchmark", "leaderboard.csv"))
lb = lb[lb.submitted_by.astype(str).str.startswith("baseline")]
conds = [(tr, ti, ta) for ta in ("seacoal", "iron_oxide") for tr in ("dry", "moist") for ti in ("ideal", "lab", "plant")]
H = np.full((len(methods), len(conds)), np.nan)
for i, m in enumerate(methods):
    for j, (tr, ti, ta) in enumerate(conds):
        v = lb[(lb.method == m) & (lb.track == tr) & (lb.tier == ti) & (lb.target == ta)].detection_limit_pct
        H[i, j] = float(v.iloc[0])
fig, axes = plt.subplots(1, 2, figsize=(W2, 2.3))
for ax, ta, rng_, title, letter in ((axes[0], "seacoal", (0.1, 5), "Seacoal", "a"), (axes[1], "iron_oxide", (0.01, 2), "Red iron oxide", "b")):
    cols = [j for j, c in enumerate(conds) if c[2] == ta]
    sub = H[:, cols]
    norm = matplotlib.colors.LogNorm(vmin=rng_[0], vmax=rng_[1])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("b", SEQ[1:])
    ax.imshow(np.where(np.isnan(sub), np.nan, sub), cmap=cmap, norm=norm, aspect="auto")
    for i in range(sub.shape[0]):
        for j in range(sub.shape[1]):
            v = sub[i, j]
            if np.isnan(v):
                ax.add_patch(plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor="#f0f0ee", edgecolor="#bbbbbb", hatch="////", lw=0))
                ax.text(j, i, "n.r.", ha="center", va="center", fontsize=6.5, color="#555555")
            else:
                ax.text(j, i, f"{v:g}", ha="center", va="center", fontsize=7,
                        color="white" if norm(v) > 0.55 else "#111111")
    ax.set_xticks(range(len(cols)), [f"{conds[j][0]}\n{conds[j][1]}" for j in cols], fontsize=6.5)
    ax.set_yticks(range(len(methods)), methods if letter == "a" else [""] * len(methods), fontsize=6.8)
    ax.tick_params(top=False, right=False, length=0)
    ax.grid(False)
    ax.set_title(f"{title}: detection limit (% of dry mix)", fontsize=8)
    ax.set_xticks(np.arange(-0.5, len(cols)), minor=True)
    ax.set_yticks(np.arange(-0.5, len(methods)), minor=True)
    ax.grid(which="minor", color="white", linewidth=1.5)
    ax.tick_params(which="minor", length=0)
fig.tight_layout(w_pad=0.4)
save(fig, "fig8_lod_heatmap")

# ------------------------------------------------------------------ PLSR predicted vs true (dry lab)
fig, axes = plt.subplots(1, 2, figsize=(W2, 2.5))
pls_diag = {}
for ax, ta, letter, lim in ((axes[0], "seacoal", "a", 5.3), (axes[1], "iron_oxide", "b", 2.12)):
    name = f"GSNIR-bench-v1.0_dry_lab_{ta}"
    cal = pd.read_csv(os.path.join(ROOT, "benchmark", "sets", f"{name}_calibration.csv.gz"))
    test = pd.read_csv(os.path.join(ROOT, "benchmark", "sets", f"{name}_test.csv.gz"))
    rc = [c for c in cal.columns if c.startswith("R_")]
    mdl = g.benchmark.baselines()["PLSR"]().fit(cal[rc].to_numpy(), cal[f"{ta}_pct"].to_numpy())
    p = mdl.score(test[rc].to_numpy())
    yt = test[f"{ta}_pct"].to_numpy()
    ax.scatter(yt + np.random.default_rng(0).normal(0, 0.006 * lim, len(yt)), p, s=3, alpha=0.35, color=C[0], lw=0)
    med = pd.Series(p).groupby(yt).median()
    ax.plot(med.index, med.values, color=C[1], marker="o", ms=3, label="Median prediction")
    ax.plot([0, lim], [0, lim], color="#555555", ls="--", lw=0.8, label="1:1")
    _, lod, thr = g.benchmark.score_levels(p, yt)
    ax.axhline(thr, color=C[2], lw=0.9, ls=":", label=f"Alarm threshold ({thr:.2f}%)")
    ax.set(xlabel=f"True {NAMES[ta].lower()} (% of dry mix)", ylabel=f"PLSR predicted (%)", xlim=(-0.1, lim), ylim=(-1, lim * 1.15))
    ax.legend(loc="upper left", fontsize=6.3)
    panel(ax, letter)
    rmsep = float(np.sqrt(np.mean((p - yt) ** 2)))
    pls_diag[ta] = (thr, rmsep, mdl.res["n_components"], mdl.res["rmsecv"], mdl.res["r2cv"])
fig.tight_layout(w_pad=1.0)
save(fig, "fig9_plsr_pred")
M("thrSc", f"{pls_diag['seacoal'][0]:.2f}")
M("thrFe", f"{pls_diag['iron_oxide'][0]:.2f}")
M("rmsepSc", f"{pls_diag['seacoal'][1]:.2f}")
M("rmsepFe", f"{pls_diag['iron_oxide'][1]:.2f}")

# ------------------------------------------------------------------ sensitivity dot plot
sens = pd.DataFrame(S["benchmark"]["sensitivity"])
sd = sens[sens.track == "dry"]
scen = list(dict.fromkeys(sd.scenario))
fig, ax = plt.subplots(figsize=(W1, 3.0))
yy = np.arange(len(scen))[::-1]
for k, (ta, lab_) in enumerate((("seacoal", "Seacoal"), ("iron_oxide", "Red iron oxide"))):
    v = [sd[(sd.scenario == s_) & (sd.target == ta)].PLSR_detection_limit_pct.iloc[0] for s_ in scen]
    ax.plot(v, yy + (0.12 if k == 0 else -0.12), ls="none", marker="o" if k == 0 else "s", ms=5, color=C[k],
            mec="white", mew=0.6, label=lab_)
ax.set_xscale("log")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{v:g}"))
ax.set_yticks(yy, [(x[0].upper() + x[1:]).replace(" um", r" $\mu$m") for x in scen], fontsize=7)
ax.set_xlim(0.05, 6)
ax.set_xlabel("PLSR detection limit, dry sand, lab noise (%)")
ax.legend(loc="lower right", fontsize=6.5)
save(fig, "fig10_sensitivity")

# ------------------------------------------------------------------ TABLES
def write(name, body):
    open(os.path.join(TAB, name + ".tex"), "w").write(body)


L_ = S["library"]
rows = []
src = {"silica_sand": "Assumed (AFS GFN 50--60)", "clay": "Assumed (aggregates)", "seacoal": "Fitted to lab AUC",
       "iron_oxide": "Fitted to lab AUC"}
for k in ORDER:
    fn = {"silica_sand": "Quartz GDS74 (Ottawa sand)", "clay": "Montmorillonite SWy-1",
          "seacoal": "Kerogen BK-Cornell", "iron_oxide": r"Hematite GDS69, $<$10\,$\mu$m"}[k]
    rows.append(rf"{NAMES[k]} & {fn} & {L_['density'][k]:.2f} & {g_(L_['grain_um'][k])} & {src[k]} \\")
write("tab_endmembers", "\n".join(rows))

T = rules["noise_tiers"]
write("tab_noise", "\n".join(rf"{k.capitalize()} & {v['snr']:,} & {v['multiplicative_sd']:.3f} & {v['offset_sd']:.3f} & {v['slope_sd']:.3f} \\"
                             for k, v in T.items()))

cand = pd.DataFrame(S["lab_calibration_candidates"])
def short(x):
    x = {"carbon_black": "Carbon black", "hematite_GDS27_bright": "GDS27", "hematite_FE2602": "FE2602",
         "s07_ASD_Kerogen_BK-Cornell_BECKa_AREF.txt": "Kerogen", "s07_ASD_Hematite_GDS69.g_lt10um_BECKb_AREF.txt": "GDS69 $<$10 µm"}.get(x, x)
    return x.replace("s07_ASD_", "").replace("_BECKa_AREF.txt", "").replace("_BECKb_AREF.txt", "").replace("_lt10um", " <10 µm").replace("_", " ").replace("µ", r"$\mu$")
write("tab_candidates", "\n".join(
    rf"{short(r.seacoal_spectrum)} & {short(r.iron_oxide_spectrum)} & {r.seacoal_um:.1f} & {('$\\geq$300$^{\\ddagger}$' if r.iron_oxide_um >= 299 else f'{r.iron_oxide_um:.2f}')} & {r.rmse_with_offsets:.1f} & {max(r.max_iron_oxide_auc, 0):.0f} \\"
    for r in cand.itertuples()))
write("tab_loo", "\n".join(rf"{r['left_out_dc2']} & {r['seacoal_um']:.1f} & {r['iron_oxide_um']:.2f} & {r['rmse']:.1f} \\" for r in loo))

tr = pd.DataFrame(S["lab_trends"]["results"])
labels = ["Calibrated (default)", "Assumed sizes, no lab calibration", "Linear mixing"]
write("tab_trends", "\n".join(
    rf"{lab_} & {r.PC1_seacoal_median_pct:.2f} & {r.PC1_iron_oxide_median_pct:.2f} & {r.rho_PC1_seacoal:.2f} & {r.rho_PC1_iron_oxide:.2f} & {r.AUC_monotone_share:.2f} & {r.AUC_rmse_vs_lab_with_group_offsets:.0f} & {r.T1} & {r.T2} & {r.T3} & {r.T4} & {r.T5} \\"
    for lab_, r in zip(labels, tr.itertuples())).replace("PASS", r"\cmark").replace("FAIL", r"\xmark"))
for lab_, r in zip(["Cal", "Usgs", "Lin"], tr.itertuples()):
    M(f"trends{lab_}", r.trends_reproduced.split("/")[0])
    M(f"pcSc{lab_}", f"{r.PC1_seacoal_median_pct:.2f}")
    M(f"pcFe{lab_}", f"{r.PC1_iron_oxide_median_pct:.2f}")

rows = []
for m in methods:
    cells = []
    for (trk, ti, ta) in conds:
        v = lb[(lb.method == m) & (lb.track == trk) & (lb.tier == ti) & (lb.target == ta)].iloc[0]
        s_ = g_(v.detection_limit_pct)
        if s_ == "n.r." and not np.isnan(v.lowest_level_detected):
            s_ = rf"n.r.$^{{\dagger}}$"
        best = np.nanmin(H[:, conds.index((trk, ti, ta))])
        if not np.isnan(v.detection_limit_pct) and v.detection_limit_pct == best:
            s_ = rf"\textbf{{{s_}}}"
        cells.append(s_)
    rows.append(m.replace("RandomForest", "Random forest").replace("GradientBoosting", "Gradient boosting") + " & " + " & ".join(cells) + r" \\")
write("tab_lod", "\n".join(rows))

pl = lb[lb.method == "PLSR"]
write("tab_plsr", "\n".join(
    rf"{ta.replace('_', ' ').capitalize()} & {trk} & {ti} & {int(r.n_components)} & {r.rmsecv:.3f} & {r.r2cv:.3f} & {g_(r.detection_limit_pct)} \\"
    for ta in ("seacoal", "iron_oxide") for trk in ("dry", "moist") for ti in ("ideal", "lab", "plant")
    for r in [pl[(pl.target == ta) & (pl.track == trk) & (pl.tier == ti)].iloc[0]]))
for ta, tn in (("seacoal", "Sc"), ("iron_oxide", "Fe")):
    for trk in ("dry", "moist"):
        for ti in ("ideal", "lab", "plant"):
            r = pl[(pl.target == ta) & (pl.track == trk) & (pl.tier == ti)].iloc[0]
            M(f"lod{tn}{trk.capitalize()}{ti.capitalize()}", g_(r.detection_limit_pct))
            M(f"rmsecv{tn}{trk.capitalize()}{ti.capitalize()}", f"{r.rmsecv:.2f}")
            M(f"rtwo{tn}{trk.capitalize()}{ti.capitalize()}", f"{r.r2cv:.3f}")

write("tab_sens", "\n".join(
    rf"{(s_[0].upper() + s_[1:]).replace(' um', r' $\mu$m')} & {g_(sd[(sd.scenario == s_) & (sd.target == 'seacoal')].PLSR_detection_limit_pct.iloc[0])} & "
    rf"{sd[(sd.scenario == s_) & (sd.target == 'seacoal')].rmsecv.iloc[0]:.3f} & "
    rf"{g_(sd[(sd.scenario == s_) & (sd.target == 'iron_oxide')].PLSR_detection_limit_pct.iloc[0])} & "
    rf"{sd[(sd.scenario == s_) & (sd.target == 'iron_oxide')].rmsecv.iloc[0]:.3f} \\" for s_ in scen))
sm = sens[sens.track == "moist"]
for s_, nm in (("calibrated default", "Def"), ("calibrated default, water path factor 4", "Pf")):
    M(f"moistSc{nm}", g_(sm[(sm.scenario == s_) & (sm.target == "seacoal")].PLSR_detection_limit_pct.iloc[0]))
    M(f"moistFe{nm}", g_(sm[(sm.scenario == s_) & (sm.target == "iron_oxide")].PLSR_detection_limit_pct.iloc[0]))
for s_, nm in (("linear mixing", "Lin"), ("seacoal = carbon black", "Cb"), ("clay = calcium montmorillonite SAz-1", "Saz"),
               ("clay grain 30 um", "Clay"), ("instrument FWHM 25 nm", "Fwhm"), ("assumed sizes (no lab calibration)", "Usgs")):
    M(f"sensSc{nm}", g_(sd[(sd.scenario == s_) & (sd.target == "seacoal")].PLSR_detection_limit_pct.iloc[0]))
    M(f"sensFe{nm}", g_(sd[(sd.scenario == s_) & (sd.target == "iron_oxide")].PLSR_detection_limit_pct.iloc[0]))

write("tab_labdata", "\n".join(
    rf"{r.sample_id.replace('+', '+')} & {'Seacoal' if r.add == 'seacoal' else 'RIO'} & {r.dc2_pct} & {r.additive_pct:g} & {r.AUC:.1f} & {r.model_AUC:.1f} & {r.group_offset:.1f} & {r.residual:+.1f} \\"
    for r in fit.itertuples()))

# worked example
i17 = int(np.argmin(abs(wl - 1700)))
mv = np.array([0.885, 0.08, 0.03, 0.005])
Rv = np.array([E.spectra[o][i17] for o in ORDER])
wv = g.mixing.reflectance_to_ssa(Rv)
av = mv / np.array([E.density[o] for o in ORDER]) / np.array([E.grain_um[o] for o in ORDER])
fv = av / av.sum()
wm = float(fv @ wv)
Rm = float(g.mixing.ssa_to_reflectance(wm))
write("tab_worked", "\n".join(
    rf"{NAMES[o]} & {mv[k]:.3f} & {E.density[o]:.2f} & {g_(E.grain_um[o])} & {Rv[k]:.5f} & {wv[k]:.5f} & {av[k] * 1e3:.4f} & {fv[k]:.4f} \\"
    for k, o in enumerate(ORDER)))
M("wMix", f"{wm:.5f}")
M("RMix", f"{Rm:.5f}")
M("xsSand", f"{fv[0]:.2f}")
M("xsClay", f"{fv[1]:.2f}")
M("xsSc", f"{fv[2]:.2f}")
M("xsFe", f"{fv[3]:.2f}")

# general numbers
B = S["benchmark"]
M("nDry", f"{L_['n_dry']:,}".replace(",", "{,}"))
M("nMoist", f"{L_['n_moist']:,}".replace(",", "{,}"))
M("nTotal", f"{L_['n_dry'] + L_['n_moist']:,}".replace(",", "{,}"))
M("nNative", f"{L_['n_native_channels']:,}".replace(",", "{,}"))
M("nInst", str(L_["n_instrument_channels"]))
M("nCal", str(B["n_cal"]))
M("nTestBlank", str(B["n_test_blank"]))
M("nTestLevel", str(B["n_test_per_level"]))
M("nSets", str(len(conds)))
M("nTestSc", f"{B['n_test_blank'] + B['n_test_per_level'] * len(B['levels']['seacoal']):,}".replace(",", "{,}"))
M("nTestFe", f"{B['n_test_blank'] + B['n_test_per_level'] * len(B['levels']['iron_oxide']):,}".replace(",", "{,}"))
M("levelsSc", ", ".join(f"{x:g}" for x in B["levels"]["seacoal"]))
M("levelsFe", ", ".join(f"{x:g}" for x in B["levels"]["iron_oxide"]))
M("feFullShare", f"{100 * L_['iron_oxide_monotone_share_full']:.1f}")
M("snrIdeal", f"{T['ideal']['snr']:,}".replace(",", "{,}"))
M("snrLab", f"{T['lab']['snr']:,}".replace(",", "{,}"))
M("snrPlant", str(T["plant"]["snr"]))
spots = L_["spot_rows"]
M("spotId", spots[2]["sample_id"])
M("spotR", f"{spots[2]['R1700']:.5f}")
pw = pc[(pc.track == "dry") & (pc.tier == "lab") & (pc.method == "PLSR")]
M("powScThree", f"{float(pw[(pw.target == 'seacoal') & np.isclose(pw.level, 0.3)].power.iloc[0]):.2f}")
M("powFeFive", f"{float(pw[(pw.target == 'iron_oxide') & np.isclose(pw.level, 0.05)].power.iloc[0]):.2f}")
sv = pc[(pc.track == "dry") & (pc.tier == "lab") & (pc.method == "SVM-RBF") & (pc.target == "seacoal")]
M("svmFive", f"{float(sv[np.isclose(sv.level, 5.0)].power.iloc[0]):.2f}")
M("svmOne", f"{float(sv[np.isclose(sv.level, 1.0)].power.iloc[0]):.2f}")
rf_ = pc[(pc.track == "dry") & (pc.tier == "lab") & (pc.method == "RandomForest") & (pc.target == "iron_oxide")]
M("rfFeTwo", f"{float(rf_[np.isclose(rf_.level, 2.0)].power.iloc[0]):.2f}")

with open(os.path.join(OUT, "macros.tex"), "w") as fh:
    fh.write("% Generated by code/09_preprint_assets.py from paper/stats.json. Do not edit by hand.\n")
    for k, v in macros.items():
        fh.write(f"\\newcommand{{\\{k}}}{{{v}}}\n")
print(f"{len(macros)} macros, figures in {FIG}, tables in {TAB}")
