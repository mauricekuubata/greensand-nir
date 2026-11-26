#!/usr/bin/env python3
"""Step 6: figures and the public leaderboard page.

Plain-language summary: draws the five figures used in the README and paper
(paper/figures/*.png) and writes the leaderboard web page
(docs/leaderboard/index.html). Every figure carries a DRAFT stamp until you
approve the package; then run this script with --final to remove it.
"""

import argparse
import html
import json
import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker  # noqa: E402,F401
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402

FIG = os.path.join(ROOT, "paper", "figures")
PROC = os.path.join(ROOT, "data", "processed")
STATS = os.path.join(ROOT, "paper", "stats.json")

# reference palette (dataviz skill), light mode
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
INK, INK2, MUTED, GRID, SURF = "#0b0b0b", "#52514e", "#8a8984", "#e6e5e1", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": MUTED, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "lines.linewidth": 1.6,
    "axes.titlesize": 10, "axes.titlecolor": INK, "axes.titleweight": "bold", "axes.titlelocation": "left",
    "legend.frameon": False,
})


def stamp(fig, final):
    if not final:
        fig.text(0.99, 0.01, "DRAFT - not verified", ha="right", va="bottom", fontsize=8, color="#e34948",
                 alpha=0.9, weight="bold")


def save(fig, name, final):
    stamp(fig, final)
    fig.savefig(os.path.join(FIG, name), dpi=200, bbox_inches="tight")
    plt.close(fig)


def fig1_endmembers(rules, final):
    E = g.io.load_endmembers(rules, os.path.join(ROOT, "data", "raw", "splib07_selected"))
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    labels = {"silica_sand": "Silica sand (quartz, Ottawa)", "clay": "Bentonite (montmorillonite SWy-1)",
              "iron_oxide": "Iron oxide (hematite GDS69 <10 um)", "seacoal": "Seacoal stand-in (kerogen)"}
    for i, k in enumerate(["silica_sand", "clay", "iron_oxide", "seacoal"]):
        ax.plot(E.wl, E.spectra[k], color=SERIES[i], label=labels[k])
        ax.annotate(labels[k].split(" (")[0], (E.wl[-1], E.spectra[k][-1]), xytext=(4, 0),
                    textcoords="offset points", va="center", fontsize=8, color=INK2)
    for x, t in ((1410, "OH"), (1910, "H2O"), (2205, "Al-OH")):
        ax.axvline(x, color=GRID, lw=0.8, zorder=0)
        ax.text(x, 0.98, t, ha="center", va="top", fontsize=7, color=MUTED, transform=ax.get_xaxis_transform())
    ax.set(xlabel="Wavelength (nm)", ylabel="Reflectance", ylim=(0, 0.9), xlim=(1000, 2350))
    ax.set_title("Reference spectra used to compute the library (USGS splib07)")
    ax.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=2, fontsize=8)
    save(fig, "fig1_reference_spectra.png", final)


def fig2_library(final):
    comp = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_compositions.csv"))
    spec = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_spectra_native1nm.csv.gz"))
    wl = np.array([float(c[2:]) for c in spec.columns[1:]])
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
    for ax, (col, levels, fixed, title) in zip(axes, [
        ("seacoal_pct", [0, 1, 2, 3, 4, 5], {"iron_oxide_pct": 0.0}, "Seacoal 0 to 5% (8% clay, no iron oxide)"),
        ("iron_oxide_pct", [0, 0.4, 0.8, 1.2, 1.6, 2.0], {"seacoal_pct": 0.0}, "Iron oxide 0 to 2% (8% clay, no seacoal)")]):
        for i, L in enumerate(levels):
            sel = (comp.clay_pct == 8) & np.isclose(comp[col], L)
            for k, v in fixed.items():
                sel &= np.isclose(comp[k], v)
            r = spec.loc[sel.to_numpy()].iloc[0, 1:].to_numpy(float)
            ax.plot(wl, r, color=SEQ[i + 1], lw=1.4)
            if i in (0, len(levels) - 1):
                ax.annotate(f"{L:g}%", (wl[-1], r[-1]), xytext=(3, 0), textcoords="offset points", va="center",
                            fontsize=8, color=INK2)
        ax.set_title(title, fontsize=9)
        ax.set_xlabel("Wavelength (nm)")
        ax.set_xlim(1000, 2350)
    axes[0].set_ylabel("Computed reflectance")
    fig.suptitle("Library examples: darker lines carry more additive", x=0.01, ha="left", fontsize=10,
                 weight="bold", color=INK)
    fig.tight_layout()
    save(fig, "fig2_library_examples.png", final)


def fig3_lab(final):
    df = pd.read_csv(os.path.join(PROC, "lab_calibration_fit.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    for ax, col, title in ((axes[0], "model_AUC", "Computed AUC alone"),
                           (axes[1], "model_plus_offset", "With one shared offset per DC2 group")):
        for i, (add, lab) in enumerate((("seacoal", "Seacoal"), ("iron_oxide", "Red iron oxide"))):
            d = df[df["add"] == add]
            ax.scatter(d[col], d.AUC, s=30, color=SERIES[i], edgecolor=SURF, linewidth=1.2, label=lab, zorder=3)
        ax.plot([0, 600], [0, 600], color=MUTED, lw=1, ls="--", zorder=1)
        r = np.sqrt(np.mean((df[col] - df.AUC) ** 2))
        ax.set_title(f"{title}\nRMSE {r:.0f} AUC units", fontsize=9)
        ax.set_xlabel("Computed AUC (absorbance x nm)")
        ax.set_xlim(0, 600)
        ax.set_ylim(0, 600)
    axes[0].set_ylabel("Measured AUC, Kuubata (2025)")
    axes[0].legend(loc="upper left")
    fig.suptitle("Computed vs measured relative AUC, 24 dry lab mixtures", x=0.01, ha="left", fontsize=10,
                 weight="bold", color=INK)
    fig.tight_layout()
    save(fig, "fig3_lab_comparison.png", final)


def fig4_power(final):
    c = pd.read_csv(os.path.join(ROOT, "benchmark", "power_curves.csv"))
    methods = ["PLSR", "PCA-LDA", "SVM-RBF", "RandomForest", "GradientBoosting"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    for ax, tgt, title in ((axes[0], "seacoal", "Seacoal"), (axes[1], "iron_oxide", "Red iron oxide")):
        for i, m in enumerate(methods):
            d = c[(c.track == "dry") & (c.tier == "lab") & (c.target == tgt) & (c.method == m)]
            ax.plot(d.level, d.power, marker="o", ms=3.5, color=SERIES[i], label=m)
        ax.axhline(0.95, color=INK2, lw=0.8, ls=":")
        ax.set_xscale("log")
        ax.text(0.03, 0.915, "95% detection", fontsize=7, color=INK2, transform=ax.get_yaxis_transform())
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.set_title(f"{title} (dry sand, lab noise)", fontsize=9)
        ax.set_xlabel("Additive level (% of dry mix, log scale)")
    axes[0].set_ylabel("Share of samples detected\n(false alarms held at 5%)")
    axes[1].legend(loc="lower right", fontsize=7)
    fig.suptitle("Detection power by method", x=0.01, ha="left", fontsize=10, weight="bold", color=INK)
    fig.tight_layout()
    save(fig, "fig4_detection_power.png", final)


def fig5_lod(final):
    lb = pd.read_csv(os.path.join(ROOT, "benchmark", "leaderboard.csv"))
    lb = lb[lb.submitted_by.str.startswith("baseline")]
    p = lb[lb.method == "PLSR"]
    tiers = ["ideal", "lab", "plant"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.0), sharey=False)
    for ax, tgt, title in ((axes[0], "seacoal", "Seacoal"), (axes[1], "iron_oxide", "Red iron oxide")):
        x = np.arange(len(tiers))
        for j, (track, lab) in enumerate((("dry", "Dry"), ("moist", "Moist (2-5%)"))):
            v = [p[(p.target == tgt) & (p.tier == t) & (p.track == track)].detection_limit_pct.iloc[0] for t in tiers]
            ax.bar(x + (j - 0.5) * 0.36, np.nan_to_num(v), width=0.34, color=SERIES[j], label=lab)
            for xi, vi in zip(x + (j - 0.5) * 0.36, v):
                ax.text(xi, 0 if pd.isna(vi) else vi, "not reached" if pd.isna(vi) else f"{vi:g}",
                        ha="center", va="bottom", fontsize=7, color=INK2)
        ax.set_xticks(x, ["Ideal", "Lab", "Plant floor"])
        ax.set_title(f"{title}: PLSR detection limit", fontsize=9)
        ax.set_ylabel("% of dry mix")
        ax.grid(axis="x", visible=False)
    axes[0].legend(loc="upper left", fontsize=8)
    fig.tight_layout()
    save(fig, "fig5_detection_limits.png", final)


def leaderboard_page(final):
    lb = pd.read_csv(os.path.join(ROOT, "benchmark", "leaderboard.csv"))
    st = json.load(open(STATS))
    lb = lb.sort_values(["target", "track", "tier", "detection_limit_pct"], na_position="last")
    rows = []
    for _, r in lb.iterrows():
        lod = "not reached" if pd.isna(r.detection_limit_pct) else f"{r.detection_limit_pct:g}"
        low = "" if pd.isna(r.get("lowest_level_detected", np.nan)) else f"{r.lowest_level_detected:g}"
        miss = "yes" if str(r.get("misses_higher_levels", "")).lower() == "true" else ""
        url = r.get("url", "")
        method = html.escape(r.method)
        if isinstance(url, str) and url.startswith(("https://", "http://")):
            method = f"<a href='{html.escape(url, quote=True)}'>{method}</a>"
        rows.append(f"<tr data-target='{html.escape(str(r.target), quote=True)}' data-track='{html.escape(str(r.track), quote=True)}' "
                    f"data-tier='{html.escape(str(r.tier), quote=True)}'><td>{html.escape(r.target.replace('_', ' '))}</td>"
                    f"<td>{html.escape(str(r.track))}</td><td>{html.escape(str(r.tier))}</td><td>{method}</td><td class='num'>{lod}</td>"
                    f"<td class='num'>{low}</td><td>{miss}</td><td>{html.escape(str(r.submitted_by))}</td></tr>")
    tiers = st["benchmark"]["tiers"]
    banner = "" if final else "<div class='draft'>DRAFT: results not yet verified by the author. Do not cite.</div>"
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Green Sand NIR Detection-Limit Leaderboard</title>
<style>
:root{{--surface:#fcfcfb;--ink:#0b0b0b;--ink2:#52514e;--muted:#8a8984;--grid:#e6e5e1;--accent:#2a78d6}}
@media (prefers-color-scheme:dark){{:root{{--surface:#1a1a19;--ink:#f0efec;--ink2:#c3c2b7;--muted:#8f8e86;--grid:#33332f;--accent:#3987e5}}}}
body{{font-family:system-ui,-apple-system,Segoe UI,sans-serif;background:var(--surface);color:var(--ink);max-width:980px;margin:2rem auto;padding:0 1rem;line-height:1.5}}
h1{{font-size:1.5rem;margin-bottom:.2rem}} p{{color:var(--ink2)}} a{{color:var(--accent)}}
.draft{{border:1px solid #e34948;color:#e34948;padding:.5rem .8rem;border-radius:6px;margin:1rem 0;font-weight:600}}
.filters{{display:flex;gap:.8rem;flex-wrap:wrap;margin:1rem 0}} select{{padding:.3rem;font:inherit;background:var(--surface);color:var(--ink);border:1px solid var(--grid);border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-size:.9rem}} th,td{{text-align:left;padding:.4rem .5rem;border-bottom:1px solid var(--grid)}}
th{{color:var(--ink2);font-weight:600}} td.num{{text-align:right;font-variant-numeric:tabular-nums}} tr:hover td{{background:color-mix(in srgb,var(--accent) 8%,transparent)}}
code{{font-size:.85em}}
</style></head><body>
<h1>Green Sand NIR Detection-Limit Leaderboard</h1>
<p>Which additive levels can a near-infrared method actually detect in foundry green sand? Every method is scored by one rule:
the alarm is set so at most 5% of clean sand samples trigger it, and the detection limit is the lowest additive level caught in at least 95% of samples, at that level and every level above it.
Spectra are computed (Hapke mixing of USGS splib07 reference spectra, calibrated to measured lab data), resampled to a 1000-2350 nm InGaAs instrument.</p>
{banner}
<p><b>Noise tiers:</b> ideal (signal-to-noise {tiers['ideal']['snr']}:1, no packing effects); lab ({tiers['lab']['snr']}:1, {tiers['lab']['multiplicative_sd']*100:g}% packing gain variation); plant floor ({tiers['plant']['snr']}:1, {tiers['plant']['multiplicative_sd']*100:g}%).
<b>Tracks:</b> dry sand; moist sand (2-5% water). Levels are percent of the dry mix.</p>
<div class="filters">
<label>Additive <select id="f-target"><option value="">all</option><option value="seacoal">seacoal</option><option value="iron_oxide">iron oxide</option></select></label>
<label>Track <select id="f-track"><option value="">all</option><option>dry</option><option>moist</option></select></label>
<label>Noise <select id="f-tier"><option value="">all</option><option>ideal</option><option>lab</option><option>plant</option></select></label>
</div>
<table><thead><tr><th>Additive</th><th>Track</th><th>Noise</th><th>Method</th><th>Detection limit (%)</th><th>Lowest level detected (%)</th><th>Misses higher levels</th><th>Submitted by</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
<h2 style="font-size:1.1rem;margin-top:2rem">Submit a method</h2>
<p>Download a set from <code>benchmark/sets/</code>, train on the <code>_calibration</code> file, score every row of the <code>_test</code> file
(higher score = more additive; do not use the test composition columns), then run
<code>python code/score_submission.py --set &lt;set name&gt; --scores your_scores.csv --method "name" --submitted-by "you" --append</code>
and open a pull request. Test labels are public, so the leaderboard runs on trust; methods are expected to share code.</p>
<p>Project: <a href="https://github.com/mauricekuubata/greensand-nir">github.com/mauricekuubata/greensand-nir</a>. Maintainer: Maurice Kuubata (ORCID 0009-0003-3178-5971).</p>
<script>
const f=['target','track','tier'].map(k=>document.getElementById('f-'+k));
function apply(){{document.querySelectorAll('tbody tr').forEach(tr=>{{tr.style.display=f.every(s=>!s.value||tr.dataset[s.id.slice(2)]===s.value)?'':'none'}})}}
f.forEach(s=>s.addEventListener('change',apply));
</script>
</body></html>"""
    os.makedirs(os.path.join(ROOT, "docs", "leaderboard"), exist_ok=True)
    open(os.path.join(ROOT, "docs", "leaderboard", "index.html"), "w").write(page)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true", help="remove DRAFT stamps (only after author verification)")
    a = ap.parse_args()
    os.makedirs(FIG, exist_ok=True)
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    fig1_endmembers(rules, a.final)
    fig2_library(a.final)
    fig3_lab(a.final)
    fig4_power(a.final)
    fig5_lod(a.final)
    leaderboard_page(a.final)
    print("figures written to paper/figures; leaderboard at docs/leaderboard/index.html")


if __name__ == "__main__":
    main()
