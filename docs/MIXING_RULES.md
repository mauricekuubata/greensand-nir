# Mixing rules

*Plain-language summary: this page explains, step by step, how one library spectrum is computed, with a worked example you can repeat in a spreadsheet. Every rule lives in `config/mixing_rules.json`; change a value there and re-run the pipeline to rebuild everything.*

## The materials (stand-ins from USGS splib07)

| Component | USGS spectrum used | Density (g/cm3) | Effective grain size (um) | How the size was set |
|---|---|---|---|---|
| Silica sand | s07_ASD_Quartz_GDS74_Sand_Ottawa_BECKc_AREF.txt | 2.65 | 250.0 | assumed (AFS GFN about 50-60) |
| Bentonite | s07_ASD_Montmorillonite_SWy-1_BECKb_AREF.txt | 2.35 | 10.0 | assumed (clay aggregates) |
| Seacoal | s07_ASD_Kerogen_BK-Cornell_BECKa_AREF.txt | 1.3 | 37.7 | fitted to your 24 lab AUC values |
| Red iron oxide | s07_ASD_Hematite_GDS69.g_lt10um_BECKb_AREF.txt | 5.26 | 2.48 | fitted to your 24 lab AUC values |

**Composition basis:** clay, seacoal and iron oxide are mass percent of the dry mixture; silica sand is the balance; moisture is mass percent of the wet mixture.

## Why not just average the spectra?

Small, dark particles block far more light than their weight suggests. So the rule (Hapke mixing) works in *single-scattering albedo* w: the chance light survives one encounter with a grain. Albedo averages by each material's share of grain cross-section, and cross-section share is proportional to mass fraction / (density x grain size). Check: on a measured USGS mixture of 2% hematite + 98% quartz, Hapke mixing fits with error 0.0112 against 0.0222 for simple averaging (at 1000 nm: measured 0.776, Hapke 0.803, averaging 0.881).

## The formula, in four steps

1. Reflectance R to albedo: g = (1 - R) / (1 + R), then w = 1 - g^2
2. Cross-section weight per component: a = mass fraction / (density x grain size), then share f = a / sum(a)
3. Mixture albedo: w_mix = sum(f x w)
4. Back to reflectance: g = sqrt(1 - w_mix), then R = (1 - g) / (1 + g)

## Worked example: library row GSNIR-v1.0-02462 (8% clay, 3% seacoal, 0.5% iron oxide) at 1700 nm

| Component | Mass fraction | Density | Grain (um) | R at 1700 nm | Albedo w | a = m/(rho d) | Share f |
|---|---|---|---|---|---|---|---|
| Silica sand | 0.885 | 2.65 | 250.0 | 0.64859 | 0.95456 | 0.001336 | 0.23291 |
| Bentonite | 0.080 | 2.35 | 10.0 | 0.76638 | 0.98251 | 0.003404 | 0.59354 |
| Seacoal | 0.030 | 1.3 | 37.7 | 0.03941 | 0.14591 | 0.000612 | 0.10672 |
| Iron oxide | 0.005 | 5.26 | 2.48 | 0.39249 | 0.80966 | 0.000383 | 0.06683 |

Mixture albedo w_mix = 0.87516. Reflectance R = **0.47784**. The library file `library/v1.0/GSNIR-v1.0_spectra_native1nm.csv.gz`, row GSNIR-v1.0-02462, column `R_1700`, holds 0.47784.

## Water (moisture extension)

Water is a thin film on every grain. Its thickness comes from mass balance (water volume / total grain surface; surface ~ 6 x mass / (density x grain size)). Each grain's albedo is multiplied by exp(-2 x alpha x thickness x path factor), where alpha is liquid water's absorption (Segelstein 1981). Path factor = 1.0 (pure geometry). For the reference recipe (8% clay, 3% seacoal, 0.5% iron oxide), reflectance at 1940 nm falls from 0.4303 dry to 0.4039 at 3.5% moisture.

## Instrument

Avantes AvaSpec-NIR256-2.5TEC (256-pixel InGaAs, TE-cooled) with AvaSphere-50 integrating sphere, as used in Kuubata (2025). Range 1000-2350 nm, 6.93 nm channel spacing (matches the pixel spacing in your Appendix D), Gaussian response 15 nm wide. Noise tiers (signal-to-noise for a perfect white reflector; packing variation as gain, offset and tilt):

| Tier | SNR | Gain sd | Offset sd | Tilt sd |
|---|---|---|---|---|
| ideal | 10000 | 0.0 | 0.0 | 0.0 |
| lab | 2000 | 0.01 | 0.002 | 0.002 |
| plant | 500 | 0.03 | 0.005 | 0.005 |
