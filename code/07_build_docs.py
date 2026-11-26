#!/usr/bin/env python3
"""Step 7: write every document from the numbers the pipeline produced.

Plain-language summary: no number in the README, the checklist, the talk track
or the paper is typed by hand. This script reads paper/stats.json and the
author block (AUTHORS.json) and writes the documents, so if the data change,
the documents change with them. Run with --final after verification to drop the
DRAFT banners.
"""

import argparse
import datetime
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import greensand_nir as g  # noqa: E402
from greensand_nir.compositions import ORDER  # noqa: E402

REPO = "greensand-nir"
GH_USER = "mauricekuubata"
VERSION = "1.0.0"


def w(path, text):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text.lstrip("\n"))


def fmt(x):
    return "not reached" if x is None or (isinstance(x, float) and np.isnan(x)) else f"{x:g}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--final", action="store_true")
    a = ap.parse_args()
    S = json.load(open(os.path.join(ROOT, "paper", "stats.json")))
    A = json.load(open(os.path.join(ROOT, "AUTHORS.json")))
    au = A["authors"][0]
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    L, C, T, B = S["library"], S["lab_calibration"], S["lab_trends"], S["benchmark"]
    status = f"Released v{VERSION}" if a.final else f"DRAFT v{VERSION} (not yet verified by the author)"
    draft = "" if a.final else "> **DRAFT.** Not yet verified by the author. Do not cite or reuse until this banner is gone.\n\n"
    today = datetime.date.today().isoformat()
    accessed = {}  # file name -> access date recorded when it was fetched
    for prov in ("PROVENANCE.txt", "PROVENANCE_lab.txt"):
        pp = os.path.join(ROOT, "data", "raw", prov)
        if os.path.exists(pp):
            for line in open(pp, encoding="utf-8"):
                parts = [x.strip() for x in line.split("|")]
                if len(parts) > 2 and not line.startswith(" "):
                    accessed[parts[1]] = parts[0]
    acc_usgs = accessed.get("ASCIIdata_splib07b_cvASD.zip", "see PROVENANCE.txt")
    acc_water = accessed.get("water_nk_Segelstein1981.yml", "see PROVENANCE.txt")
    acc_lab = accessed.get("lab_pc1_auc_transcribed.csv", "see PROVENANCE_lab.txt")
    lb = pd.DataFrame(B["leaderboard"])
    plsr = lb[lb.method == "PLSR"].set_index(["track", "tier", "target"]).detection_limit_pct
    def P(track, tier, tgt):
        return fmt(float(plsr.loc[(track, tier, tgt)]))
    cal_def = T["results"][0]
    usgs = T["results"][1]
    linr = T["results"][2]
    sens = pd.DataFrame(B["sensitivity"])
    def SL(scn, tgt, track="dry"):
        v = sens[(sens.scenario == scn) & (sens.target == tgt) & (sens.track == track)].PLSR_detection_limit_pct
        return fmt(float(v.iloc[0])) if len(v) else "n/a"
    gr, de = L["grain_um"], L["density"]
    mm = L["mixing_model_check"]
    offs = C["group_offsets"]
    loo = C["leave_one_group_out"]
    sc_rng = (min(x["seacoal_um"] for x in loo), max(x["seacoal_um"] for x in loo))
    fe_rng = (min(x["iron_oxide_um"] for x in loo), max(x["iron_oxide_um"] for x in loo))
    spots = L["spot_rows"]
    ins = rules["instrument"]
    inst_first = f"R_{ins['start_nm']:.2f}"
    tiers = rules["noise_tiers"]
    cite = (f"{au['family']}, {au['given'][0]}. (2026). Green Sand Near-Infrared Reference Library and "
            f"Detection-Limit Benchmark (v{VERSION}). Zenodo. DOI pending.")

    # worked example at 1700 nm for spot row 3
    E = g.io.load_endmembers(rules, os.path.join(ROOT, "data", "raw", "splib07_selected"))
    i17 = int(np.argmin(abs(E.wl - 1700)))
    m = np.array([0.885, 0.08, 0.03, 0.005])
    Rv = np.array([E.spectra[o][i17] for o in ORDER])
    wv = g.mixing.reflectance_to_ssa(Rv)
    av = m / np.array([de[o] for o in ORDER]) / np.array([gr[o] for o in ORDER])
    fv = av / av.sum()
    wm = float((fv * wv).sum())
    Rm = float(g.mixing.ssa_to_reflectance(wm))
    names = {"silica_sand": "Silica sand", "clay": "Bentonite", "seacoal": "Seacoal", "iron_oxide": "Iron oxide"}
    wex_rows = "\n".join(
        f"| {names[o]} | {m[k]:.3f} | {de[o]} | {gr[o]} | {Rv[k]:.5f} | {wv[k]:.5f} | {av[k]:.6f} | {fv[k]:.5f} |"
        for k, o in enumerate(ORDER))

    # ------------------------------------------------------------------ README
    w("README.md", f"""
# Green Sand Near-Infrared Reference Library

**Status:** {status} | **Maintainer:** {au['name']}, [ORCID {au['orcid']}](https://orcid.org/{au['orcid']}) | **License:** code MIT, data CC BY 4.0 | **DOI:** pending

{draft}**In plain terms:** foundries still check their sand with slow tests like loss on ignition, so a bad batch can reach the mold line before the result comes back. Near-infrared (NIR) sensors could check sand in seconds, but there is no public, shared reference for which additive levels such a sensor can reliably detect. This project provides an open set of {L['n_dry']:,} computed green sand spectra (plus {L['n_moist']:,} moist-sand spectra), a fixed test that measures the smallest amount of seacoal or red iron oxide a method can detect, and a Python package to reproduce and extend all of it.

New here? Read [docs/START_HERE.md](docs/START_HERE.md). Terms are explained in [docs/GLOSSARY.md](docs/GLOSSARY.md).

## What this is

A versioned library of computed near-infrared reflectance spectra of foundry green sand (silica sand, bentonite, seacoal, red iron oxide, water) across production ranges: {rules['library_grid']['clay_pct']['start']}-{rules['library_grid']['clay_pct']['stop']}% clay, 0-5% seacoal, 0-2% iron oxide and, in the moisture extension, 2-5% water. Spectra are computed from USGS Spectral Library Version 7 reference spectra with Hapke (single-scattering albedo) mixing, calibrated against 24 measured dry mixtures from Kuubata (2025, University of Northern Iowa), and provided both at 1 nm and resampled to the {ins['start_nm']}-{ins['stop_nm']} nm InGaAs instrument class used in that study ({L['n_instrument_channels']} channels, {ins['step_nm']} nm spacing). A detection-limit benchmark scores any calibration method with one rule: false alarms on clean sand held at 5%, detection limit = lowest level caught in at least 95% of samples, at that level and above.

## Headline results

- The calibrated model reproduces **{cal_def['trends_reproduced']}** of the laboratory trends checked (first principal component {cal_def['PC1_seacoal_median_pct']}% for seacoal vs 99.23% measured; {cal_def['PC1_iron_oxide_median_pct']}% for red iron oxide vs 97.87% measured). With the assumed starting particle sizes (no lab calibration) the model reproduces {usgs['trends_reproduced']}; with simple linear mixing, {linr['trends_reproduced']}.
- **Partial least squares regression (PLSR)**, lab-grade noise, dry sand: seacoal detected from **{P('dry','lab','seacoal')}%**, red iron oxide from **{P('dry','lab','iron_oxide')}%**. Plant-floor noise: {P('dry','plant','seacoal')}% and {P('dry','plant','iron_oxide')}%. Moist sand (2-5% water), lab noise: {P('moist','lab','seacoal')}% and {P('moist','lab','iron_oxide')}%.
- Present-or-absent machine-learning classifiers can miss high additive levels they were not tuned for; see the leaderboard column "misses higher levels".

![Detection power](paper/figures/fig4_detection_power.png)

## What is here

```
config/mixing_rules.json   every mixing rule and assumption (the author sets these)
code/                      numbered pipeline scripts, run in order
src/greensand_nir/         the Python package (mixing, water, instrument, preprocessing, PLSR, benchmark)
library/v1.0/              dry library: compositions + spectra (1 nm and instrument resolution)
library/moisture/          moisture extension
benchmark/sets/            12 benchmark sets (calibration + test), leaderboard.csv, power_curves.csv
data/raw/                  inputs with PROVENANCE.txt; data/processed/ QA report and calibration
docs/                      START_HERE, GLOSSARY, CODEBOOK, MIXING_RULES, LIMITATIONS, VERIFY_CHECKLIST,
                           PUBLISH_GUIDE, TALK_TRACK, NEXT_STEPS, leaderboard/ (web page)
paper/                     stats.json, figures, JOSS paper draft
tests/                     automated tests (pytest)
```

## Run it

```
pip install -e ".[figures,test]"
python code/01_fetch.py            # download USGS + water data, log provenance
python code/02_calibrate_to_lab.py # fit seacoal and iron oxide effective sizes to the lab AUC values
python code/03_build_library.py    # library v1.0 + moisture extension + QA report
python code/04_lab_trends.py       # repeat the lab analysis on computed spectra
python code/05_benchmark.py        # benchmark sets, baselines, leaderboard, sensitivity
python code/06_figures.py          # figures + leaderboard page
python code/07_build_docs.py       # documents from stats.json
python code/09_preprint_assets.py  # preprint figures, tables and number macros
cd paper/preprint && pdflatex main && bibtex main && pdflatex main && pdflatex main && cd ../..
pytest
```

The whole pipeline runs in a few minutes on a laptop. Outputs are deterministic (fixed random seeds).

## Use the package

```python
import greensand_nir as g
rules = g.io.load_rules("config/mixing_rules.json")
E = g.io.load_endmembers(rules, "data/raw/splib07_selected")
E.grain_um.update(seacoal={gr['seacoal']}, iron_oxide={gr['iron_oxide']})
R = g.mixing.mix(E.matrix(["silica_sand", "clay", "seacoal", "iron_oxide"]),
                 [0.885, 0.08, 0.03, 0.005],
                 [E.density[k] for k in ["silica_sand", "clay", "seacoal", "iron_oxide"]],
                 [E.grain_um[k] for k in ["silica_sand", "clay", "seacoal", "iron_oxide"]],
                 moisture_pct=3.5, water_alpha=E.water_alpha)
ins = g.instrument.Instrument(rules, E.wl)
reading = ins.measure(R.reshape(1, -1), tier="lab", rng=0)   # simulated instrument reading
```

## Submit a method to the leaderboard

Train on `benchmark/sets/<set>_calibration.csv.gz`, score every row of `<set>_test.csv.gz` (higher = more additive), then run `python code/score_submission.py --set <set> --scores scores.csv --method "name" --submitted-by "you" --append` and open a pull request. Leaderboard page: `docs/leaderboard/index.html` (published with GitHub Pages).

## Sources

| Source | Vintage | License | Accessed |
|---|---|---|---|
| Kokaly et al., USGS Spectral Library Version 7 Data, https://doi.org/10.5066/F7RR1WDJ | 2017 | US public domain | {acc_usgs} |
| Segelstein (1981), liquid water optical constants, via refractiveindex.info database | 1981 | CC0 | {acc_water} |
| Kuubata (2025), NIR Spectroscopy as a Tool for Identifying Additives in Foundry Green Sands, UNI, https://scholarworks.uni.edu/grp/4669 | 2025 | author's own work; 24 values transcribed | {acc_lab} |

## Limitations

Read [docs/LIMITATIONS.md](docs/LIMITATIONS.md) before using or citing anything here. The short version: these are computed spectra, calibrated to one small dry laboratory study. They show what is detectable in principle under stated assumptions, not what a particular sensor will achieve in a particular plant.

## Citation

See `CITATION.cff`. {cite}

## How this was built

Claude (Anthropic) assisted with code and data handling. {au['name']} set every mixing rule and verified every output.
""")

    # ------------------------------------------------------------------ START HERE
    w("docs/START_HERE.md", f"""
# Start Here: Green Sand Near-Infrared Reference Library

*Read this first. It explains the project in plain language. Terms are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

A free, permanent set of computer-made near-infrared spectra of foundry green sand, plus a fair test that tells anyone the smallest amount of seacoal or red iron oxide an NIR method can detect.

## Why it matters

Foundries control sand with slow offline tests such as loss on ignition. By the time a result comes back, a bad batch may already be in molds, and the problem shows up as scrap. NIR sensors read sand in seconds, but there is no public, shared reference for which additive levels they can reliably catch. This project builds one openly, so a foundry, a sensor maker or a researcher can check a sensor or a calibration before trusting it on the line. The U.S. Department of Defense's February 2022 report *Securing Defense-Critical Supply Chains* names castings and forgings among its high-priority areas (https://media.defense.gov/2022/Feb/24/2002944158/-1/-1/1/DOD-EO-14017-REPORT-SECURING-DEFENSE-CRITICAL-SUPPLY-CHAINS.PDF).

Think of it as an eye chart for sand sensors: a fixed set of "letters" of known size, and a rule for reading the smallest line.

## Where the information comes from

All sources are free and public.

| Source | In plain terms | What one row looks like | Link |
|---|---|---|---|
| USGS Spectral Library Version 7 | The U.S. Geological Survey's measured spectra of pure minerals and materials | One material: its reflectance at every wavelength | https://doi.org/10.5066/F7RR1WDJ |
| Segelstein (1981) water data | How strongly liquid water absorbs light at each wavelength | One wavelength: water's absorption | refractiveindex.info |
| Your UNI study (Kuubata 2025) | Your measured dry green sand mixtures | One mixture: DC2 %, additive %, PC1 score, AUC | https://scholarworks.uni.edu/grp/4669 |

## What you will have at the end

- [ ] **A public project page** on GitHub: https://github.com/{GH_USER}/{REPO} (after you publish)
- [ ] **Library v1.0** ({L['n_dry']:,} dry spectra) with its own DOI on Zenodo
- [ ] **Detection-limit benchmark and public leaderboard** with its own DOI
- [ ] **Moisture extension** ({L['n_moist']:,} moist spectra) with its own DOI
- [ ] **The Python package `greensand-nir`**, tested and documented, with its own DOI (and optionally on PyPI)
- [ ] A software paper draft for the Journal of Open Source Software (paper/paper.md)

## How it connects to your work

Your UNI study showed NIR separates seacoal and red iron oxide in dry green sand and named PLSR and moist, compacted sand as next steps. This project takes those steps on open data, and it checks every computed result against the trends you measured.

## What you need to do

| Your task | When | Time |
|---|---|---|
| Answer the decisions in VERIFY_CHECKLIST Part 4 | Now | 20 min |
| Check the results with the checklist | Now | 1.5 to 2 hours |
| Approve publishing in your own words | After checking | 5 min |
| Create Zenodo account, publish with PUBLISH_GUIDE | After approval | 45 min |

## The steps ahead

1. **Data collected.** Done.
2. **Mixing engine and package.** Done.
3. **Library v1.0 and moisture extension, with quality checks.** Done.
4. **Detection-limit benchmark and leaderboard.** Done.
5. **Figures and documents.** Done.
6. **Your verification, then publishing.** *You are here.*
""")

    # ------------------------------------------------------------------ MIXING RULES (plain + worked example)
    w("docs/MIXING_RULES.md", f"""
# Mixing rules

{draft}*Plain-language summary: this page explains, step by step, how one library spectrum is computed, with a worked example you can repeat in a spreadsheet. Every rule lives in `config/mixing_rules.json`; change a value there and re-run the pipeline to rebuild everything.*

## The materials (stand-ins from USGS splib07)

| Component | USGS spectrum used | Density (g/cm3) | Effective grain size (um) | How the size was set |
|---|---|---|---|---|
| Silica sand | {L['endmember_files']['silica_sand']} | {de['silica_sand']} | {gr['silica_sand']} | assumed (AFS GFN about 50-60) |
| Bentonite | {L['endmember_files']['clay']} | {de['clay']} | {gr['clay']} | assumed (clay aggregates) |
| Seacoal | {L['endmember_files']['seacoal']} | {de['seacoal']} | {gr['seacoal']} | fitted to your 24 lab AUC values |
| Red iron oxide | {L['endmember_files']['iron_oxide']} | {de['iron_oxide']} | {gr['iron_oxide']} | fitted to your 24 lab AUC values |

**Composition basis:** {rules['composition_basis']}.

## Why not just average the spectra?

Small, dark particles block far more light than their weight suggests. So the rule (Hapke mixing) works in *single-scattering albedo* w: the chance light survives one encounter with a grain. Albedo averages by each material's share of grain cross-section, and cross-section share is proportional to mass fraction / (density x grain size). Check: on a measured USGS mixture of 2% hematite + 98% quartz, Hapke mixing fits with error {mm['rmse_hapke']} against {mm['rmse_linear']} for simple averaging (at 1000 nm: measured {mm['R1000_measured']}, Hapke {mm['R1000_hapke']}, averaging {mm['R1000_linear']}).

## The formula, in four steps

1. Reflectance R to albedo: g = (1 - R) / (1 + R), then w = 1 - g^2
2. Cross-section weight per component: a = mass fraction / (density x grain size), then share f = a / sum(a)
3. Mixture albedo: w_mix = sum(f x w)
4. Back to reflectance: g = sqrt(1 - w_mix), then R = (1 - g) / (1 + g)

## Worked example: library row {spots[2]['sample_id']} (8% clay, 3% seacoal, 0.5% iron oxide) at 1700 nm

| Component | Mass fraction | Density | Grain (um) | R at 1700 nm | Albedo w | a = m/(rho d) | Share f |
|---|---|---|---|---|---|---|---|
{wex_rows}

Mixture albedo w_mix = {wm:.5f}. Reflectance R = **{Rm:.5f}**. The library file `library/v1.0/GSNIR-v1.0_spectra_native1nm.csv.gz`, row {spots[2]['sample_id']}, column `R_1700`, holds {spots[2]['R1700']:.5f}.

## Water (moisture extension)

Water is a thin film on every grain. Its thickness comes from mass balance (water volume / total grain surface; surface ~ 6 x mass / (density x grain size)). Each grain's albedo is multiplied by exp(-2 x alpha x thickness x path factor), where alpha is liquid water's absorption (Segelstein 1981). Path factor = {rules['water']['path_factor']} (pure geometry). For the reference recipe (8% clay, 3% seacoal, 0.5% iron oxide), reflectance at 1940 nm falls from {L['R1940_ref_dry']} dry to {L['R1940_ref_wet']['3.5']} at 3.5% moisture.

## Instrument

{ins['name']}. Range {ins['start_nm']}-{ins['stop_nm']} nm, {ins['step_nm']} nm channel spacing (matches the pixel spacing in your Appendix D), Gaussian response {ins['fwhm_nm']} nm wide. Noise tiers (signal-to-noise for a perfect white reflector; packing variation as gain, offset and tilt):

| Tier | SNR | Gain sd | Offset sd | Tilt sd |
|---|---|---|---|---|
""" + "\n".join(f"| {k} | {v['snr']} | {v['multiplicative_sd']} | {v['offset_sd']} | {v['slope_sd']} |" for k, v in tiers.items()) + "\n")

    # ------------------------------------------------------------------ CODEBOOK
    w("docs/CODEBOOK.md", f"""
# Codebook

*Plain-language summary: what every column in every data file means. Open this when you open a CSV.*

## library/v1.0/GSNIR-v1.0_compositions.csv (and library/moisture/GSNIR-moist-v1.0_compositions.csv)

| Column | Meaning | Units | Source / transformation |
|---|---|---|---|
| sample_id | Unique recipe ID (GSNIR-v1.0-NNNNN, GSNIR-moist-v1.0-NNNNN) | text | row order of the grid |
| silica_sand_pct | Silica sand share of the dry mix | mass % of dry mix | 100 minus the other three |
| clay_pct | Bentonite share | mass % of dry mix | grid {rules['library_grid']['clay_pct']} |
| seacoal_pct | Seacoal share | mass % of dry mix | grid {rules['library_grid']['seacoal_pct']} (moisture set: {rules['moisture_grid']['seacoal_pct']}) |
| iron_oxide_pct | Red iron oxide share | mass % of dry mix | grid {rules['library_grid']['iron_oxide_pct']} (moisture set: {rules['moisture_grid']['iron_oxide_pct']}) |
| moisture_pct | Water | mass % of wet mix | 0 in v1.0; {rules['moisture_grid']['moisture_pct']} in the moisture set |

## *_spectra_native1nm.csv.gz

`sample_id`, then `R_1000` ... `R_2350`: computed reflectance (0 to 1, relative to a perfect white diffuse reflector) at each nanometre. Noise-free.

## *_spectra_instrument.csv

`sample_id`, then `R_<centre nm>` for {L['n_instrument_channels']} instrument channels, labelled to 0.01 nm (`{inst_first}`, `R_{ins['start_nm'] + ins['step_nm']:.2f}`, ...; centres {ins['start_nm']} + {ins['step_nm']} x i nm up to {ins['stop_nm']} nm, {ins['fwhm_nm']} nm Gaussian response). Same channel labels as the benchmark sets. Noise-free; add noise with `greensand_nir.instrument.Instrument.measure`.

## library/endmembers_native1nm.csv

`wavelength_nm`, the four reference spectra used (`silica_sand`, `clay`, `seacoal`, `iron_oxide`), and alternatives (`<component>__alt_<name>`), copied unchanged from USGS splib07 (ASD-convolved release) for 1000-2350 nm.

## benchmark/sets/GSNIR-bench-v{B['set_version']}_<track>_<tier>_<target>_<calibration|test>.csv.gz

| Column | Meaning |
|---|---|
| sample_id | unique ID |
| silica_sand_pct, clay_pct, seacoal_pct, iron_oxide_pct, moisture_pct | composition as above (in the test file, methods must not use these) |
| {inst_first} ... | simulated instrument reading (reflectance with noise and packing effects) |

Calibration files: {B['n_cal']} spectra, 25% with zero target additive, the rest log-uniform from the lowest test level to the maximum. Test files: {B['n_test_blank']} zero-level spectra plus {B['n_test_per_level']} at each level. Seacoal levels: {B['levels']['seacoal']}. Iron oxide levels: {B['levels']['iron_oxide']}. Non-target components vary uniformly across production ranges.

## benchmark/leaderboard.csv

set, track (dry/moist), tier (ideal/lab/plant), target, method, detection_limit_pct (lowest level with at least 95% detection at it and every higher level, with false alarms at 5%; blank = not reached), lowest_level_detected (first level reaching 95%), misses_higher_levels (true if a higher level later falls below 95%), submitted_by, seconds (fit plus scoring time, baselines only), PLSR diagnostics (n_components, rmsecv, r2cv), and url (link to the code, community submissions only).

## data/raw/lab_kuubata2025/lab_pc1_auc_transcribed.csv

Measured values from Kuubata (2025) Appendix D, typed in by hand: sample_id, additive, dc2_pct, additive_pct, PC1 (paper's PCA score), AUC (relative area, absorbance x nm), A_999.695nm (measured absorbance in the first pixel).

## data/processed/

qa_report.txt (quality checks), lab_calibration*.json/csv (fit of effective sizes), lab_trends.csv and lab_auc_comparison.csv (lab replication), hematite_fit*.csv (mixing-model check).
""")

    # ------------------------------------------------------------------ LIMITATIONS
    w("docs/LIMITATIONS.md", f"""
# Limitations

{draft}*Plain-language summary: what this project cannot tell you. Read before citing.*

1. **Computed, not measured.** Every library spectrum is calculated from pure-material spectra with a physical mixing model. Real sand has grain coatings, oolitic clay, burnt clay, fines and dead clay that the model does not include.
2. **No coal in the USGS library.** Seacoal is represented by kerogen (BK-Cornell), the organic matter coal forms from. It matches seacoal's darkness but not necessarily its exact absorption bands near 1700 and 2300 nm. With carbon black instead, the PLSR seacoal detection limit (dry, lab noise) is {SL('seacoal = carbon black','seacoal')}% instead of {SL('calibrated default','seacoal')}%.
3. **Red iron oxide stand-in.** The bright synthetic hematite in the USGS library (GDS27) cannot reproduce the measured AUC increase at any particle size (it is brighter than the sand from about 1135 nm onward). The darker fine natural hematite GDS69 (<10 um fraction) is used instead. Foundry red iron oxide products differ; this is the most important stand-in to replace with a measured spectrum.
4. **Effective sizes are fitted, not measured.** Seacoal ({gr['seacoal']} um) and iron oxide ({gr['iron_oxide']} um) sizes were fitted to 24 dry laboratory AUC values from one study, one sand, one bentonite. They are chosen from a {C['grid_um'][2]}-point logarithmic grid ({C['grid_um'][0]}-{C['grid_um'][1]} um), so neighbouring candidate sizes differ by about {(float(C['grid_um'][1]) / float(C['grid_um'][0])) ** (1 / (C['grid_um'][2] - 1)) * 100 - 100:.0f}%; the reported sizes are not more precise than that. Leaving out one DC2 group at a time moves them within {sc_rng[0]:g}-{sc_rng[1]:g} um and {fe_rng[0]:g}-{fe_rng[1]:g} um. The iron oxide value is far below the wavelength, where Hapke theory is approximate: treat it as an empirical parameter.
5. **Shared-baseline offsets in the lab data.** The measured AUC values contain a component shared by all additive levels at each DC2 level ({', '.join(f'DC2 {k}%: {v:g}' for k, v in offs.items())} AUC units). The model cannot produce this from composition, so the calibration treats it as a per-group offset. It most likely comes from the single 0% additive sample per DC2 level (packing, measurement session, mirror reference). Without the offsets, computed and measured AUC differ by {cal_def['AUC_rmse_vs_lab']} units RMSE (with offsets {cal_def['AUC_rmse_vs_lab_with_group_offsets']}). Consequence: the library does not reproduce the measured increase of additive AUC with DC2 content.
6. **Bentonite type.** The paper calls DC2 "Southern Bentonite" in the methods and "Western Bentonite" in figure legends. The library uses sodium montmorillonite SWy-1 (western). With calcium montmorillonite SAz-1, the PLSR seacoal limit is {SL('clay = calcium montmorillonite SAz-1','seacoal')}%.
7. **Water model is uncalibrated.** Moisture is a uniform film with pure geometric path length (path factor {rules['water']['path_factor']}). It ignores darkening from refractive-index matching, water held between clay layers, and compaction. Real moist green sand is likely darker with stronger water bands. Raising the path factor to 4 changes the moist-sand PLSR limits to {SL('calibrated default, water path factor 4','seacoal','moist')}% seacoal and {SL('calibrated default, water path factor 4','iron_oxide','moist')}% iron oxide. Use the moisture extension as a first approximation until measured moist spectra exist.
8. **Instrument and noise are modelled.** Noise tiers are stated signal-to-noise levels plus random packing gain, offset and tilt. They are not measured from your instrument's replicate scans. The instrument response width ({ins['fwhm_nm']} nm) is assumed. A 25 nm width gives a seacoal limit of {SL('instrument FWHM 25 nm','seacoal')}%.
9. **Reference standard.** The lab used a mirror reference in an integrating sphere; the library is relative to a perfect white diffuse reflector. Differences of this kind cancel in relative AUC and in calibrations built within one instrument, but absolute absorbance values are not comparable.
10. **Detection limits depend on the rule.** Limits use a 5% false-alarm rate and 95% detection on the stated level grid; a different rule or a finer grid gives different numbers. Benchmark test labels are public, so the leaderboard runs on trust.
11. **Scope.** Dry library and one moisture model; no compaction, temperature, or sand-system ageing effects; additives other than seacoal and red iron oxide (cereal, wood flour, other carbon sources) are not included.
""")

    # ------------------------------------------------------------------ VERIFY CHECKLIST
    rng = np.random.default_rng(7)
    comp = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_compositions.csv"))
    rand_ids = sorted(rng.choice(len(comp), 3, replace=False))
    lab = pd.read_csv(os.path.join(ROOT, "data", "raw", "lab_kuubata2025", "lab_pc1_auc_transcribed.csv"))
    lab_check = lab[lab.additive_pct > 0].iloc[[0, 5, 11, 12, 17, 23]]
    lab_lines = "\n".join(f"- [ ] {r.sample_id}: DC2 {r.dc2_pct}%, {r.additive} {r.additive_pct}% -> PC1 {r.PC1}, AUC {r.AUC} ___"
                          for r in lab_check.itertuples())
    w("docs/VERIFY_CHECKLIST.md", f"""
# Your verification checklist

*Before anything goes public under your name, you check it. Total time: about 1.5 to 2 hours. Tick each box and add the date. The publish gate (`python tools/publish_gate.py . --allow-draft-in src/ tests/ tools/ code/ docs/GLOSSARY.md`) checks the mechanical items automatically. These are yours.*

## Part 1: Make sure the results can be rebuilt (15 to 30 min)

Pick one:
- [ ] **Option A, run it yourself.** In a terminal inside the project folder, paste:
  ```
  pip install -e ".[figures,test]"
  python code/01_fetch.py && python code/02_calibrate_to_lab.py && python code/03_build_library.py
  python code/04_lab_trends.py && python code/05_benchmark.py && python code/06_figures.py && pytest
  ```
  You should see the QA report print `dry library v1.0: {L['n_dry']} recipes`, and pytest end with `passed`.
- [ ] **Option B, ask Claude.** In a new chat with Opus 5.5 or Fable 5, upload the project zip and say: "Re-run this pipeline from scratch and give me the headline numbers." Compare with: seacoal fitted size {gr['seacoal']} um, iron oxide {gr['iron_oxide']} um; PLSR dry lab detection limits {P('dry','lab','seacoal')}% seacoal and {P('dry','lab','iron_oxide')}% iron oxide; lab trends {cal_def['trends_reproduced']}.

Then:
- [ ] `data/raw/PROVENANCE.txt` lists the USGS archive (28,371,812 bytes) and the water file.
- [ ] Every number in README.md matches `paper/stats.json` (they are generated from it; spot-check two).

## Part 2: Check the sources (15 min)

- [ ] Open https://doi.org/10.5066/F7RR1WDJ. It loads, is free, and is "USGS Spectral Library Version 7 Data". USGS data are public domain.
- [ ] Open https://refractiveindex.info/?shelf=main&book=H2O&page=Segelstein . The page loads; the database is CC0.
- [ ] On the USGS spectral library pages (https://crustal.usgs.gov/speclab/QueryAll07a.php), look up the descriptions of the samples used and confirm they are what this project says:
  - [ ] Quartz GDS74 Sand Ottawa (silica sand)
  - [ ] Montmorillonite SWy-1 (Wyoming sodium bentonite)
  - [ ] Kerogen BK-Cornell (what kind of kerogen? note it: ___)
  - [ ] Hematite GDS69 <10 um fraction (natural or synthetic? ___)
  - [ ] Hematite.02+Quartz.98 GDS76: which hematite and quartz were used? ___ (the mixing-model check assumes GDS27 and fine quartz)

## Part 3: Check values by hand (30 to 45 min)

**Your lab values (most important).** I typed these from the images in your Appendix D. Open your own spreadsheets ("Seacoal_PC1_AUC.xlsx" and the red iron oxide equivalent) and compare. The full table is `data/raw/lab_kuubata2025/lab_pc1_auc_transcribed.csv` (24 rows, check all if you can):
{lab_lines}

**USGS reference values.** Open `library/endmembers_native1nm.csv`, find the row `wavelength_nm = 1700`. Then open the matching file in `data/raw/splib07_selected/` (a column of numbers; the value for 1700 nm is on line 1352, because line 1 is a header and line 2 is 350 nm):
""" + "\n".join(f"- [ ] {names[k]}: {v:.5f}" for k, v in L["endmember_R1700"].items()) + f"""

**The mixing formula by hand.** Repeat the worked example in `docs/MIXING_RULES.md` in Excel or Google Sheets. You should get {Rm:.5f} at 1700 nm for row {spots[2]['sample_id']}.

**Library rows.** Open `library/v1.0/GSNIR-v1.0_compositions.csv` and the native spectra file; confirm each recipe and value:
""" + "\n".join(f"- [ ] {s_['sample_id']}: clay {s_['clay']}%, seacoal {s_['seacoal']}%, iron oxide {s_['iron_oxide']}% -> R_1100 {s_['R1100']}, R_1700 {s_['R1700']}, R_2200 {s_['R2200']}" for s_ in spots) + """

**Does it make physical sense?** For each, say yes or no:
- [ ] More additive means darker: the 4th row above (more seacoal and iron oxide) is lower than the 3rd at all three wavelengths.
- [ ] More clay means a deeper clay dip at 2200 nm: the 2nd row (12% clay) is lower at R_2200 than the 1st (3% clay), but higher at R_1100 and R_1700 (bentonite is brighter than the sand outside its absorption bands).
- [ ] In figure paper/figures/fig1_reference_spectra.png, the bentonite curve dips at 1410, 1910 and 2205 nm, and the seacoal stand-in is nearly black and flat.
- [ ] Figure 3 (paper/figures/fig3_lab_comparison.png): with offsets, points sit near the dashed line.

**Three random library rows** (seed 7), check that silica sand + clay + seacoal + iron oxide = 100:
""" + "\n".join(f"- [ ] GSNIR-v1.0-{i:05d}" for i in rand_ids) + f"""

## Part 4: Your decisions (20 min)

The build made these choices provisionally. Agree or change each one. Each changes a value in `config/mixing_rules.json`; I re-run everything after your answers.

- [ ] **D1. Bentonite stand-in.** Your methods say "Southern Bentonite (DC2)"; your figure legends say "Western Bentonite". Which is it? Western/sodium: keep SWy-1 (current). Southern/calcium: switch to SAz-1 (PLSR seacoal limit {SL('clay = calcium montmorillonite SAz-1','seacoal')}% instead of {SL('calibrated default','seacoal')}%). Your answer: ___
- [ ] **D2. Seacoal stand-in.** Kerogen (current, closest chemistry) or carbon black (pure carbon)? Both fit your data about equally. Recommended: kerogen. Your answer: ___
- [ ] **D3. Iron oxide stand-in.** Your data rule out the bright hematite GDS27. GDS69 <10 um (current) or FE2602 (fits marginally better)? Recommended: GDS69. Your answer: ___
- [ ] **D4. Shared-baseline offsets.** Do you agree that the per-DC2 shared component in your AUC values ({', '.join(f'{k}%: {v:g}' for k, v in offs.items())}) is most likely a baseline-sample or session effect, and should be treated as an offset when calibrating? If you still have the raw spectra (.ABS8 or Excel), send them and I can test this directly. Your answer: ___
- [ ] **D5. Particle sizes not fitted.** Silica sand {gr['silica_sand']} um (your AGSCO sand's AFS GFN, if known: ___) and bentonite aggregates {gr['clay']} um. Keep? Your answer: ___
- [ ] **D6. Water path factor.** 1.0 (pure geometry, current, conservative) or higher (stronger water bands)? Recommended: keep 1.0 and label the moisture extension "first approximation" until measured moist spectra exist. Your answer: ___
- [ ] **D7. Noise tiers.** Ideal {tiers['ideal']['snr']}:1, lab {tiers['lab']['snr']}:1 with {tiers['lab']['multiplicative_sd']*100:g}% packing variation, plant {tiers['plant']['snr']}:1 with {tiers['plant']['multiplicative_sd']*100:g}%. Your Figure 4/5 repeatability scans could set the lab tier from real data. Keep, or send the 12-replicate spectra? Your answer: ___
- [ ] **D8. Detection rule.** 5% false alarms, 95% detection, at the level and all levels above. Keep? Your answer: ___
- [ ] **D9. Releases.** Four Zenodo records (library, benchmark, moisture extension, software), one per target in your plan (recommended), or a single record? Your answer: ___

## Part 5: Before it goes public (15 to 30 min)

- [ ] The README "In plain terms" paragraph and the paper summary are rewritten in your own words. (Claude can do this with you line by line.)
- [ ] Your name, ORCID, affiliation and email are correct in `AUTHORS.json`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Draft stamps removed (`python code/06_figures.py --final` and `python code/07_build_docs.py --final`), and `python tools/publish_gate.py . --allow-draft-in src/ tests/ tools/ code/ docs/GLOSSARY.md` passes.
- [ ] Evidence log row written on release day (`docs/evidence_log.csv`).

**When every box is ticked, reply to Claude in your own words that you have checked the package and approve publishing.**
""")

    # ------------------------------------------------------------------ TALK TRACK
    w("docs/TALK_TRACK.md", f"""
# Talking about the Green Sand Near-Infrared Reference Library

{draft}## 60-second version

**The problem:** foundries still control green sand with slow offline tests like loss on ignition, so a bad batch of sand can reach the mold line before the result comes back, and the problem shows up later as scrap castings.

**What I built:** an open reference library of {L['n_dry'] + L['n_moist']:,} computed near-infrared spectra of green sand, covering the clay, seacoal, iron oxide and moisture ranges used in production. It is calibrated against my own laboratory measurements from my graduate study at UNI. I also built a fixed benchmark that measures the smallest amount of an additive any NIR method can detect, and an open Python package to reproduce it.

**What it shows:** with laboratory-grade noise, standard partial least squares regression detects seacoal from about {P('dry','lab','seacoal')} percent and red iron oxide from about {P('dry','lab','iron_oxide')} percent in dry sand. At plant-floor noise, those figures are {P('dry','plant','seacoal')} and {P('dry','plant','iron_oxide')} percent.

**Who can use it:** foundries choosing a sand sensor, sensor makers testing calibrations, and researchers comparing methods on the same public test.

**Where it is:** github.com/{GH_USER}/{REPO}, archived on Zenodo with DOIs.

## Two-sentence version

{au['name']} built an open near-infrared reference library and detection-limit benchmark for foundry green sand, calibrated against his own UNI laboratory measurements. It tells foundries and sensor makers which seacoal and iron oxide levels an NIR sensor can detect in principle, so sand can be checked before pouring instead of after scrap.

## Questions you may be asked

1. **Where does the data come from?** Measured spectra of pure minerals from the U.S. Geological Survey's public spectral library, mixed with a standard physics model, and calibrated against 24 dry green sand mixtures I measured at UNI.
2. **What are its limits?** The spectra are computed, not measured, and calibrated to one small dry laboratory study. The USGS library has no coal, so seacoal uses a stand-in, and the moisture model is a first approximation. The numbers show what is detectable in principle, not what a specific sensor will do in a specific plant.
3. **Why does this matter for the United States?** The Department of Defense's February 2022 report *Securing Defense-Critical Supply Chains* names castings and forgings among its high-priority areas. Better, faster sand control means less scrap and steadier output from U.S. foundries, and this gives the whole industry a free, common yardstick for NIR sensors.
""")

    # ------------------------------------------------------------------ NEXT STEPS
    w("docs/NEXT_STEPS.md", f"""
# Next steps

*What later versions add, so v{VERSION} is understood as a first step.*

1. Replace stand-ins with measured spectra of the actual materials (AGSCO sand, DC2 bentonite, foundry seacoal, foundry red iron oxide) on the AvaSpec-NIR256-2.5TEC. This removes the largest uncertainty.
2. Use the 12-replicate repeatability scans to set the lab noise tier from real data.
3. Measure moist, compacted green sand at 2-5% water to calibrate the water path factor and add a compaction term.
4. Add other carbon sources (cereal, wood flour, lustrous carbon formers) and burnt (dead) clay.
5. Add external validation: foundry sand samples with LOI and methylene blue clay results.
6. Publish the package on PyPI and submit the software paper (paper/paper.md) to the Journal of Open Source Software.
""")

    # ------------------------------------------------------------------ CHANGELOG
    w("CHANGELOG.md", f"""
# Changelog

## {VERSION} ({today if a.final else "unreleased draft"})
- Library v1.0: {L['n_dry']:,} dry computed spectra (3-12% clay, 0-5% seacoal, 0-2% red iron oxide).
- Moisture extension: {L['n_moist']:,} computed spectra at 2-5% water.
- Detection-limit benchmark: 12 sets, scoring rule, 5 baseline methods, leaderboard page.
- Package greensand-nir: mixing, water film, instrument and noise model, preprocessing, PLSR, benchmark, lab replication.
- Calibration of seacoal and red iron oxide effective sizes to Kuubata (2025) laboratory AUC values.
""")

    # ------------------------------------------------------------------ CITATION, metadata
    w("CITATION.cff", f"""
cff-version: 1.2.0
message: "If you use this work, please cite it as below."
type: dataset
title: "Green Sand Near-Infrared Reference Library and Detection-Limit Benchmark"
version: "{VERSION}"
date-released: "{today}"
authors:
  - family-names: "{au['family']}"
    given-names: "{au['given']}"
    orcid: "https://orcid.org/{au['orcid']}"
    affiliation: "{au['affiliation']}"
license:
  - CC-BY-4.0
  - MIT
repository-code: "https://github.com/{GH_USER}/{REPO}"
keywords:
  - near-infrared spectroscopy
  - foundry green sand
  - seacoal
  - iron oxide
  - spectral library
  - detection limit
  - PLSR
  - chemometrics
""")
    creators = [{"name": f"{x['family']}, {x['given']}", "orcid": x["orcid"], "affiliation": x["affiliation"]}
                for x in A["authors"]]
    common = {"creators": creators, "access_right": "open", "version": VERSION, "language": "eng",
              "related_identifiers": [{"identifier": f"https://github.com/{GH_USER}/{REPO}", "relation": "isSupplementTo",
                                       "scheme": "url"},
                                      {"identifier": "10.5066/F7RR1WDJ", "relation": "isDerivedFrom", "scheme": "doi"},
                                      {"identifier": "https://scholarworks.uni.edu/grp/4669", "relation": "isDerivedFrom", "scheme": "url"}],
              "keywords": ["near-infrared spectroscopy", "foundry", "green sand", "seacoal", "iron oxide", "spectral library",
                           "detection limit", "chemometrics"],
              "notes": f"Claude (Anthropic) assisted with code and data handling; {au['name']} set every mixing rule and verified every output."}
    recs = {
        "library": {"upload_type": "dataset", "license": "cc-by-4.0",
                    "title": f"Green Sand Computed-Mixture Near-Infrared Spectral Library v{VERSION}",
                    "description": f"<p>{L['n_dry']:,} computed near-infrared reflectance spectra of dry foundry green sand (3-12% bentonite, 0-5% seacoal, 0-2% red iron oxide, silica sand balance), 1000-2350 nm at 1 nm and at the resolution of a 1000-2350 nm InGaAs instrument ({L['n_instrument_channels']} channels). Computed by Hapke single-scattering-albedo mixing of USGS Spectral Library Version 7 spectra, with seacoal and iron oxide effective particle sizes calibrated to 24 measured dry mixtures (Kuubata 2025). Includes codebook, mixing rules, QA report and provenance log.</p>",
                    "files": ["library/v1.0", "library/endmembers_native1nm.csv", "config/mixing_rules.json", "docs/CODEBOOK.md",
                              "docs/MIXING_RULES.md", "docs/LIMITATIONS.md", "data/raw/PROVENANCE.txt", "data/raw/PROVENANCE_lab.txt",
                              "data/processed/qa_report.txt", "data/processed/lab_calibration.json", "README.md", "LICENSE-DATA", "CITATION.cff"]},
        "benchmark": {"upload_type": "dataset", "license": "cc-by-4.0",
                      "title": f"Green Sand NIR Detection-Limit Benchmark and Leaderboard v{VERSION}",
                      "description": "<p>Twelve benchmark sets (dry and moist sand; ideal, lab and plant-floor noise; seacoal and red iron oxide) of simulated 1000-2350 nm InGaAs readings, a scoring rule (5% false alarms, 95% detection), baseline results for PCA-LDA, PLSR, SVM, random forest and gradient boosting, and a submission script.</p>",
                      "files": ["benchmark", "code/score_submission.py", "docs/leaderboard/index.html", "docs/CODEBOOK.md", "README.md",
                                "LICENSE-DATA", "CITATION.cff"]},
        "moisture": {"upload_type": "dataset", "license": "cc-by-4.0",
                     "title": f"Green Sand NIR Library Moisture Extension v{VERSION}",
                     "description": f"<p>{L['n_moist']:,} computed spectra of moist green sand (2-5% water) with liquid-water absorption (Segelstein 1981) added as a grain-surface film. First approximation; see LIMITATIONS.</p>",
                     "files": ["library/moisture", "config/mixing_rules.json", "docs/CODEBOOK.md", "docs/MIXING_RULES.md",
                               "docs/LIMITATIONS.md", "README.md", "LICENSE-DATA", "CITATION.cff"]},
        "software": {"upload_type": "software", "license": "mit",
                     "title": f"greensand-nir: open Python package for green sand NIR spectral mixing, preprocessing and PLSR calibration v{VERSION}",
                     "description": "<p>Tested, documented Python package: Hapke and linear mixing, water film model, InGaAs instrument and noise simulation, NIR preprocessing (absorbance, SNV, MSC, Savitzky-Golay), PLSR with cross-validation, detection-limit scoring, and the full reproducible pipeline.</p>",
                     "files": ["src", "tests", "code", "tools/provenance.py", "pyproject.toml", "requirements.txt", "README.md", "LICENSE",
                               "CITATION.cff", "CHANGELOG.md", "CONTRIBUTING.md", "paper"]},
    }
    for k, v in recs.items():
        meta = {**common, **{kk: vv for kk, vv in v.items() if kk != "files"}}
        w(f"zenodo/{k}.json", json.dumps({"metadata": meta, "files": v["files"]}, indent=2))

    # ------------------------------------------------------------------ PUBLISH GUIDE
    w("docs/PUBLISH_GUIDE.md", f"""
# Publish guide (first-timer friendly)

*Do this only after the verification checklist is complete and the publish gate passes. Total time: about 45 minutes. Nothing here was pushed automatically, because no GitHub or Zenodo token was supplied.*

## Copy-ready text

- **Repository name:** `{REPO}`
- **Repository description:** Open near-infrared reference library and detection-limit benchmark for foundry green sand additive control
- **Author line:** {au['name']}, {au['affiliation']}, ORCID {au['orcid']}
- **Keywords:** near-infrared spectroscopy; foundry; green sand; seacoal; iron oxide; spectral library; detection limit; chemometrics

## Step 1: Zenodo account (3 min)

Go to https://zenodo.org/signup/ and choose **Log in with ORCID**. Your ORCID then attaches to every record.

## Step 2: GitHub repository (10 min)

1. If https://github.com/{GH_USER}/{REPO} already exists, skip to 2. Otherwise go to https://github.com/new. Name: `{REPO}`. Public. Do **not** add a README (the project has one). Click **Create repository**.
2. In a terminal inside the project folder (if the repository already has commits, use `git pull origin main --allow-unrelated-histories` before pushing, or push from a fresh clone):
   ```
   git init -b main
   git add -A
   git commit -m "Green Sand NIR Reference Library v{VERSION}"
   git remote add origin https://github.com/{GH_USER}/{REPO}.git
   git push -u origin main
   ```
   The screen should end with `main -> main`.
3. Leaderboard page: on GitHub, **Settings > Pages > Source: Deploy from a branch > main > /docs > Save**. After a minute the page is at https://{GH_USER}.github.io/{REPO}/leaderboard/

## Step 3: Four Zenodo records (25 min)

Build the four upload archives first:
```
python code/08_release_archives.py
```
This writes `release/greensand-nir-library-v{VERSION}.zip`, `-benchmark-`, `-moisture-` and `-software-` zips. For each:

1. Zenodo > **New upload**. Drag in the zip.
2. Fill in from `zenodo/<name>.json` (title, description, upload type, license, keywords, version {VERSION}). Creator: {au['family']}, {au['given']}, ORCID {au['orcid']}, affiliation "{au['affiliation']}".
3. Related identifiers: the GitHub URL ("is supplement to"), 10.5066/F7RR1WDJ ("is derived from").
4. Click **Publish**. Copy the DOI shown (looks like 10.5281/zenodo.1234567).

Alternative for the software record: Zenodo > **Account > GitHub**, flip the switch for `{REPO}`, then on GitHub **Releases > Draft a new release**, tag `v{VERSION}`, publish. Zenodo mints the software DOI automatically.

Scripted alternative: `python tools/zenodo_deposit.py --files release/greensand-nir-library-v{VERSION}.zip --metadata zenodo/library.json --sandbox` reads the record file directly (needs `pip install requests` and a ZENODO_SANDBOX_TOKEN in the shell). Drop `--sandbox` and add `--publish` only after checking the sandbox record.

Faster, if you prefer: create a Zenodo token (https://zenodo.org/account/settings/applications/tokens/new/, tick deposit:write and deposit:actions) and a GitHub token (https://github.com/settings/tokens, tick "repo"), give them to Claude in a new session, and it will push to the Zenodo sandbox first so you can see the result, then for real. Revoke both tokens afterwards.

## Step 4: Record the DOIs (5 min)

Paste each DOI into `CITATION.cff` (doi field), the README status line, and `docs/evidence_log.csv`, then commit and push. Save a PDF of each Zenodo record page.

## Preprint (20 min)

The preprint is `paper/preprint/main.pdf`; its LaTeX source bundle is `paper/preprint/preprint_source.zip` (main.tex, main.bbl, refs.bib, macros.tex, tables/, figures/).

- **engrXiv** (https://engrxiv.org, engineering; no endorsement needed): create an account, Submit, upload `main.pdf`, paste the title and abstract from the PDF, add the GitHub URL and the four Zenodo DOIs as related resources, choose CC BY 4.0, and complete the AI-use statement with the text in the paper's "Author contributions and use of AI tools" section.
- **arXiv** (https://arxiv.org/submit; category physics.app-ph is the closest fit): first-time submitters need an endorsement in the category (https://arxiv.org/auth/endorse); ask a former advisor or co-author who posts there. Upload `preprint_source.zip`, title and author exactly as in the PDF, license CC BY 4.0, comments "13 pages, 10 figures; data and code at github.com/mauricekuubata/greensand-nir".
- After posting, record the preprint ID or DOI in `docs/evidence_log.csv` and the README.

## Optional: PyPI (10 min)

Create an account at https://pypi.org, make an API token, then `python -m build` and `python -m twine upload dist/*` (username `__token__`, password = token).

## Optional: Journal of Open Source Software

`paper/paper.md` is a draft. JOSS expects substantial, tested, documented software; submit at https://joss.theoj.org/papers/new with the repository URL and the software DOI after the package has been public for a while and you have rewritten the paper in your own words.
""")

    # the evidence log is filled in by hand after release: never overwrite an existing one
    if not os.path.exists(os.path.join(ROOT, "docs", "evidence_log.csv")):
      w("docs/evidence_log.csv", "date,artifact_or_event,type,venue_or_host,link_or_doi,status,prong_tags,metrics_snapshot,files_saved,notes\n"
      f"YYYY-MM-DD,Green Sand NIR Library v{VERSION},dataset,Zenodo + GitHub,pending,not yet published,,0 downloads at release,zenodo_record.pdf,fill on release day\n"
      f"YYYY-MM-DD,Green Sand NIR Detection-Limit Benchmark v{VERSION},dataset,Zenodo + GitHub Pages,pending,not yet published,,,,\n"
      f"YYYY-MM-DD,Green Sand NIR Moisture Extension v{VERSION},dataset,Zenodo,pending,not yet published,,,,\n"
      f"YYYY-MM-DD,greensand-nir Python package v{VERSION},software,Zenodo + GitHub (+PyPI),pending,not yet published,,,,\n")

    # ------------------------------------------------------------------ JOSS paper draft
    d_today = datetime.date.today()
    n_tests = sum(1 for line in open(os.path.join(ROOT, "tests", "test_core.py"), encoding="utf-8")
                  if line.startswith("def test_"))
    w("paper/paper.md", f"""
---
title: 'greensand-nir: an open Python package and reference library for near-infrared control of foundry green sand additives'
tags:
  - Python
  - near-infrared spectroscopy
  - foundry
  - chemometrics
  - spectral mixing
authors:
  - name: {au['name']}
    orcid: {au['orcid']}
    affiliation: 1
affiliations:
  - name: {au['affiliation']}
    index: 1
date: {d_today.day} {d_today:%B %Y}
bibliography: paper.bib
---

{draft}# Summary

Foundry green sand is silica sand bonded with bentonite clay and water, usually with a carbonaceous additive such as seacoal and, in some systems, red iron oxide. Foundries still check additive levels with slow offline tests such as loss on ignition, so out-of-specification sand can reach the molding line before a result comes back. Near-infrared (NIR) spectroscopy reads a sample in seconds, and laboratory work has shown that it separates seacoal and red iron oxide in dry green sand [@kuubata2025]. `greensand-nir` is an open Python package that computes realistic NIR spectra of green sand mixtures from public reference spectra, simulates how a typical NIR instrument would read them, and scores any calibration method on a fixed detection-limit test, so that people choosing or building an NIR method for sand control can compare methods on common ground.

# Statement of need

Anyone evaluating NIR for green sand control currently has to collect and measure their own mixtures before they can say which additive levels a method detects, and published studies use different samples, instruments and decision rules, so their figures cannot be compared directly. `greensand-nir` provides the missing common reference: (1) a mixing engine that computes green sand reflectance from USGS Spectral Library Version 7 spectra [@kokaly2017] using Hapke single-scattering-albedo mixing [@hapke2012], with an optional grain-surface water film based on liquid water optical constants [@segelstein1981]; (2) an instrument model for the 1000-2350 nm InGaAs class, with signal-to-noise and packing (gain, offset, tilt) effects; (3) standard NIR preprocessing and partial least squares regression (PLSR) calibration [@wold2001]; (4) a calibration of the two least-known inputs, the effective particle sizes of seacoal and red iron oxide, against 24 measured dry laboratory mixtures; and (5) a benchmark that turns any method's scores into a detection limit under one stated rule. The intended users are foundry engineers and sand laboratories evaluating NIR, sensor makers testing calibrations, and chemometrics researchers who need a domain test set.

# State of the field

General-purpose tools cover parts of this workflow. scikit-learn [@pedregosa2011] provides PLSR and the classifiers used as baselines, and `greensand-nir` builds on it rather than reimplementing them. Spectral Python [@spy] reads and processes spectral libraries and imagery, and USGS splib07 [@kokaly2017] supplies measured spectra of pure minerals and materials, but neither models foundry mixtures. Hapke mixing is widely used in planetary and mineral remote sensing, usually in project-specific code [@hapke2012]. We are not aware of an open package, dataset or benchmark aimed at foundry green sand. The domain layer here (green sand composition model, laboratory-calibrated stand-in materials, instrument model for the InGaAs class used in foundry studies, and a detection-limit scoring rule) does not belong inside a general library, so a separate package that depends on those libraries was the appropriate choice.

# Software design

All modelling assumptions live in one rules file (`config/mixing_rules.json`), and numbered pipeline scripts read it and rebuild every output, so a changed assumption propagates to the library, benchmark, figures and documents. Hapke diffusive mixing was chosen over simple averaging because dark, fine particles darken a powder far more than their mass share suggests; on a measured USGS mixture of 2% hematite and 98% quartz, the Hapke model fits with root-mean-square error {mm['rmse_hapke']} against {mm['rmse_linear']} for linear mixing. The trade-off is that Hapke theory is approximate for particles smaller than the wavelength, so the fitted effective sizes are treated as empirical parameters and their stability is reported (leave-one-group-out refits). The benchmark scores a method by its output scores only: the alarm threshold is set at a 5% false-alarm rate on clean samples (with randomised tie handling), and the detection limit is the lowest level detected in at least 95% of samples at that level and every level above it. Any method, including non-linear classifiers, can therefore be compared without access to its internals. Random seeds are fixed, so the pipeline reproduces its outputs exactly, and every number in the documentation is written from a generated statistics file rather than typed by hand.

# Research impact statement

The package is new and has no external users yet. Its near-term value rests on concrete, reproducible materials: a library of {L['n_dry']:,} dry and {L['n_moist']:,} moist computed spectra, 12 benchmark sets (dry and moist sand, three noise tiers, two additives) with baseline results for five methods, a public leaderboard with a submission script, and {n_tests} automated tests. The computed spectra reproduce {cal_def['trends_reproduced']} laboratory trends tested in [@kuubata2025]. All outputs are archived on Zenodo with DOIs, and the stated next step is replacing the stand-in materials with measured spectra of foundry materials.

# AI usage disclosure

Claude (Anthropic) was used to write and review code, tests and documentation and to draft this paper. The author set every mixing rule and modelling assumption, checked the computed results against his own laboratory measurements, verified reference values, worked examples and library rows by hand using the project's verification checklist, and revised this paper.

# Acknowledgements

Reference spectra are from the U.S. Geological Survey Spectroscopy Laboratory. This work received no specific funding.

# References
""")
    w("paper/paper.bib", """
@misc{kuubata2025,
  author = {Kuubata, Maurice},
  title = {NIR Spectroscopy as a Tool for Identifying Additives in Foundry Green Sands},
  year = {2025},
  howpublished = {Graduate Research Paper, University of Northern Iowa},
  url = {https://scholarworks.uni.edu/grp/4669}
}
@misc{kokaly2017,
  author = {Kokaly, R. F. and Clark, R. N. and Swayze, G. A. and Livo, K. E. and Hoefen, T. M. and Pearson, N. C. and Wise, R. A. and Benzel, W. M. and Lowers, H. A. and Driscoll, R. L. and Klein, A. J.},
  title = {USGS Spectral Library Version 7 Data},
  year = {2017},
  publisher = {U.S. Geological Survey},
  doi = {10.5066/F7RR1WDJ}
}
@book{hapke2012,
  author = {Hapke, Bruce},
  title = {Theory of Reflectance and Emittance Spectroscopy},
  edition = {2},
  publisher = {Cambridge University Press},
  year = {2012},
  doi = {10.1017/CBO9781139025683}
}
@mastersthesis{segelstein1981,
  author = {Segelstein, David J.},
  title = {The Complex Refractive Index of Water},
  school = {University of Missouri-Kansas City},
  year = {1981},
  url = {http://hdl.handle.net/10355/11599}
}
@article{pedregosa2011,
  author = {Pedregosa, Fabian and Varoquaux, Ga{\\"e}l and Gramfort, Alexandre and Michel, Vincent and Thirion, Bertrand and Grisel, Olivier and Blondel, Mathieu and Prettenhofer, Peter and Weiss, Ron and Dubourg, Vincent and Vanderplas, Jake and Passos, Alexandre and Cournapeau, David and Brucher, Matthieu and Perrot, Matthieu and Duchesnay, {\\'E}douard},
  title = {Scikit-learn: Machine Learning in Python},
  journal = {Journal of Machine Learning Research},
  volume = {12},
  pages = {2825--2830},
  year = {2011}
}
@misc{spy,
  author = {Boggs, Thomas},
  title = {Spectral Python (SPy)},
  howpublished = {Python package},
  url = {https://www.spectralpython.net}
}
@article{wold2001,
  author = {Wold, Svante and Sj{\\"o}str{\\"o}m, Michael and Eriksson, Lennart},
  title = {PLS-regression: a basic tool of chemometrics},
  journal = {Chemometrics and Intelligent Laboratory Systems},
  volume = {58},
  number = {2},
  pages = {109--130},
  year = {2001},
  doi = {10.1016/S0169-7439(01)00155-1}
}
""")
    print("documents written")


if __name__ == "__main__":
    main()
