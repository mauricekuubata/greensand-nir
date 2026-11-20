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
  You should see the QA report print `dry library v1.0: 4410 recipes`, and pytest end with `passed`.
- [ ] **Option B, ask Claude.** In a new chat with Opus 5.5 or Fable 5, upload the project zip and say: "Re-run this pipeline from scratch and give me the headline numbers." Compare with: seacoal fitted size 37.7 um, iron oxide 2.48 um; PLSR dry lab detection limits 0.5% seacoal and 0.1% iron oxide; lab trends 5/5.

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
- [ ] (S96+DC3+Sea1): DC2 3%, Seacoal 1.0% -> PC1 -8.480863, AUC 200.628 ___
- [ ] (S89+DC6+Sea5): DC2 6%, Seacoal 5.0% -> PC1 9.2644042, AUC 481.1934 ___
- [ ] (S83+DC12+Sea5): DC2 12%, Seacoal 5.0% -> PC1 16.19153, AUC 509.2637 ___
- [ ] (S96.5+DC3+RIO0.5): DC2 3%, Red Iron Oxide 0.5% -> PC1 -11.767649, AUC 102.401 ___
- [ ] (S92+DC6+RIO2): DC2 6%, Red Iron Oxide 2.0% -> PC1 9.69693, AUC 322.914 ___
- [ ] (S86+DC12+RIO2): DC2 12%, Red Iron Oxide 2.0% -> PC1 17.828391, AUC 317.9218 ___

**USGS reference values.** Open `library/endmembers_native1nm.csv`, find the row `wavelength_nm = 1700`. Then open the matching file in `data/raw/splib07_selected/` (a column of numbers; the value for 1700 nm is on line 1352, because line 1 is a header and line 2 is 350 nm):
- [ ] Silica sand: 0.64859
- [ ] Bentonite: 0.76638
- [ ] Seacoal: 0.03941
- [ ] Iron oxide: 0.39249

**The mixing formula by hand.** Repeat the worked example in `docs/MIXING_RULES.md` in Excel or Google Sheets. You should get 0.47784 at 1700 nm for row GSNIR-v1.0-02462.

**Library rows.** Open `library/v1.0/GSNIR-v1.0_compositions.csv` and the native spectra file; confirm each recipe and value:
- [ ] GSNIR-v1.0-00000: clay 3%, seacoal 0%, iron oxide 0% -> R_1100 0.65978, R_1700 0.69483, R_2200 0.58801
- [ ] GSNIR-v1.0-03969: clay 12%, seacoal 0%, iron oxide 0% -> R_1100 0.70504, R_1700 0.73533, R_2200 0.55328
- [ ] GSNIR-v1.0-02462: clay 8%, seacoal 3%, iron oxide 0.5% -> R_1100 0.45733, R_1700 0.47784, R_2200 0.42117
- [ ] GSNIR-v1.0-02645: clay 8%, seacoal 5%, iron oxide 2% -> R_1100 0.37614, R_1700 0.40784, R_2200 0.3797
- [ ] GSNIR-v1.0-00440: clay 3%, seacoal 5%, iron oxide 2% -> R_1100 0.30912, R_1700 0.34202, R_2200 0.33796

**Does it make physical sense?** For each, say yes or no:
- [ ] More additive means darker: the 4th row above (more seacoal and iron oxide) is lower than the 3rd at all three wavelengths.
- [ ] More clay means a deeper clay dip at 2200 nm: the 2nd row (12% clay) is lower at R_2200 than the 1st (3% clay), but higher at R_1100 and R_1700 (bentonite is brighter than the sand outside its absorption bands).
- [ ] In figure paper/figures/fig1_reference_spectra.png, the bentonite curve dips at 1410, 1910 and 2205 nm, and the seacoal stand-in is nearly black and flat.
- [ ] Figure 3 (paper/figures/fig3_lab_comparison.png): with offsets, points sit near the dashed line.

**Three random library rows** (seed 7), check that silica sand + clay + seacoal + iron oxide = 100:
- [ ] GSNIR-v1.0-02756
- [ ] GSNIR-v1.0-03017
- [ ] GSNIR-v1.0-04165

## Part 4: Your decisions (20 min)

The build made these choices provisionally. Agree or change each one. Each changes a value in `config/mixing_rules.json`; I re-run everything after your answers.

- [ ] **D1. Bentonite stand-in.** Your methods say "Southern Bentonite (DC2)"; your figure legends say "Western Bentonite". Which is it? Western/sodium: keep SWy-1 (current). Southern/calcium: switch to SAz-1 (PLSR seacoal limit 0.3% instead of 0.5%). Your answer: ___
- [ ] **D2. Seacoal stand-in.** Kerogen (current, closest chemistry) or carbon black (pure carbon)? Both fit your data about equally. Recommended: kerogen. Your answer: ___
- [ ] **D3. Iron oxide stand-in.** Your data rule out the bright hematite GDS27. GDS69 <10 um (current) or FE2602 (fits marginally better)? Recommended: GDS69. Your answer: ___
- [ ] **D4. Shared-baseline offsets.** Do you agree that the per-DC2 shared component in your AUC values (3%: 50.1, 6%: 171.5, 9%: 158.8, 12%: 277.8) is most likely a baseline-sample or session effect, and should be treated as an offset when calibrating? If you still have the raw spectra (.ABS8 or Excel), send them and I can test this directly. Your answer: ___
- [ ] **D5. Particle sizes not fitted.** Silica sand 250.0 um (your AGSCO sand's AFS GFN, if known: ___) and bentonite aggregates 10.0 um. Keep? Your answer: ___
- [ ] **D6. Water path factor.** 1.0 (pure geometry, current, conservative) or higher (stronger water bands)? Recommended: keep 1.0 and label the moisture extension "first approximation" until measured moist spectra exist. Your answer: ___
- [ ] **D7. Noise tiers.** Ideal 10000:1, lab 2000:1 with 1% packing variation, plant 500:1 with 3%. Your Figure 4/5 repeatability scans could set the lab tier from real data. Keep, or send the 12-replicate spectra? Your answer: ___
- [ ] **D8. Detection rule.** 5% false alarms, 95% detection, at the level and all levels above. Keep? Your answer: ___
- [ ] **D9. Releases.** Four Zenodo records (library, benchmark, moisture extension, software), one per target in your plan (recommended), or a single record? Your answer: ___

## Part 5: Before it goes public (15 to 30 min)

- [ ] The README "In plain terms" paragraph and the paper summary are rewritten in your own words. (Claude can do this with you line by line.)
- [ ] Your name, ORCID, affiliation and email are correct in `AUTHORS.json`.
- [ ] You have read `docs/LIMITATIONS.md` and agree with it.
- [ ] Draft stamps removed (`python code/06_figures.py --final` and `python code/07_build_docs.py --final`), and `python tools/publish_gate.py . --allow-draft-in src/ tests/ tools/ code/ docs/GLOSSARY.md` passes.
- [ ] Evidence log row written on release day (`docs/evidence_log.csv`).

**When every box is ticked, reply to Claude in your own words that you have checked the package and approve publishing.**
