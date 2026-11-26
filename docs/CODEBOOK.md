# Codebook

*Plain-language summary: what every column in every data file means. Open this when you open a CSV.*

## library/v1.0/GSNIR-v1.0_compositions.csv (and library/moisture/GSNIR-moist-v1.0_compositions.csv)

| Column | Meaning | Units | Source / transformation |
|---|---|---|---|
| sample_id | Unique recipe ID (GSNIR-v1.0-NNNNN, GSNIR-moist-v1.0-NNNNN) | text | row order of the grid |
| silica_sand_pct | Silica sand share of the dry mix | mass % of dry mix | 100 minus the other three |
| clay_pct | Bentonite share | mass % of dry mix | grid {'start': 3, 'stop': 12, 'step': 1} |
| seacoal_pct | Seacoal share | mass % of dry mix | grid {'start': 0, 'stop': 5, 'step': 0.25} (moisture set: {'start': 0, 'stop': 5, 'step': 0.5}) |
| iron_oxide_pct | Red iron oxide share | mass % of dry mix | grid {'start': 0, 'stop': 2, 'step': 0.1} (moisture set: {'start': 0, 'stop': 2, 'step': 0.25}) |
| moisture_pct | Water | mass % of wet mix | 0 in v1.0; {'start': 2, 'stop': 5, 'step': 0.5} in the moisture set |

## *_spectra_native1nm.csv.gz

`sample_id`, then `R_1000` ... `R_2350`: computed reflectance (0 to 1, relative to a perfect white diffuse reflector) at each nanometre. Noise-free.

## *_spectra_instrument.csv

`sample_id`, then `R_<centre nm>` for 195 instrument channels, labelled to 0.01 nm (`R_1000.00`, `R_1006.93`, ...; centres 1000 + 6.93 x i nm up to 2350 nm, 15 nm Gaussian response). Same channel labels as the benchmark sets. Noise-free; add noise with `greensand_nir.instrument.Instrument.measure`.

## library/endmembers_native1nm.csv

`wavelength_nm`, the four reference spectra used (`silica_sand`, `clay`, `seacoal`, `iron_oxide`), and alternatives (`<component>__alt_<name>`), copied unchanged from USGS splib07 (ASD-convolved release) for 1000-2350 nm.

## benchmark/sets/GSNIR-bench-v1.0_<track>_<tier>_<target>_<calibration|test>.csv.gz

| Column | Meaning |
|---|---|
| sample_id | unique ID |
| silica_sand_pct, clay_pct, seacoal_pct, iron_oxide_pct, moisture_pct | composition as above (in the test file, methods must not use these) |
| R_1000.00 ... | simulated instrument reading (reflectance with noise and packing effects) |

Calibration files: 600 spectra, 25% with zero target additive, the rest log-uniform from the lowest test level to the maximum. Test files: 200 zero-level spectra plus 100 at each level. Seacoal levels: [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]. Iron oxide levels: [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0]. Non-target components vary uniformly across production ranges.

## benchmark/leaderboard.csv

set, track (dry/moist), tier (ideal/lab/plant), target, method, detection_limit_pct (lowest level with at least 95% detection at it and every higher level, with false alarms at 5%; blank = not reached), lowest_level_detected (first level reaching 95%), misses_higher_levels (true if a higher level later falls below 95%), submitted_by, seconds (fit plus scoring time, baselines only), PLSR diagnostics (n_components, rmsecv, r2cv), and url (link to the code, community submissions only).

## data/raw/lab_kuubata2025/lab_pc1_auc_transcribed.csv

Measured values from Kuubata (2025) Appendix D, typed in by hand: sample_id, additive, dc2_pct, additive_pct, PC1 (paper's PCA score), AUC (relative area, absorbance x nm), A_999.695nm (measured absorbance in the first pixel).

## data/processed/

qa_report.txt (quality checks), lab_calibration*.json/csv (fit of effective sizes), lab_trends.csv and lab_auc_comparison.csv (lab replication), hematite_fit*.csv (mixing-model check).
