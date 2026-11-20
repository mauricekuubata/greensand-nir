# Start Here: Green Sand Near-Infrared Reference Library

*Read this first. It explains the project in plain language. Terms are explained in [GLOSSARY.md](GLOSSARY.md).*

## What you are building

A free, permanent set of computer-made near-infrared spectra of foundry green sand, plus a fair test that tells anyone the smallest amount of seacoal or red iron oxide an NIR method can detect.

## Why it matters

Foundries control sand with slow offline tests such as loss on ignition. By the time a result comes back, a bad batch may already be in molds, and the problem shows up as scrap. NIR sensors read sand in seconds, but no one has published which additive levels they can actually catch. This project answers that question openly, so a foundry, a sensor maker or a researcher can check a sensor or a calibration before trusting it on the line. The U.S. Department of Defense's February 2022 report on securing defense-critical supply chains names castings and forgings among its high-priority areas.

Think of it as an eye chart for sand sensors: a fixed set of "letters" of known size, and a rule for reading the smallest line.

## Where the information comes from

All sources are free and public.

| Source | In plain terms | What one row looks like | Link |
|---|---|---|---|
| USGS Spectral Library Version 7 | The U.S. Geological Survey's measured spectra of pure minerals and materials | One material: its reflectance at every wavelength | https://doi.org/10.5066/F7RR1WDJ |
| Segelstein (1981) water data | How strongly liquid water absorbs light at each wavelength | One wavelength: water's absorption | refractiveindex.info |
| Your UNI study (Kuubata 2025) | Your measured dry green sand mixtures | One mixture: DC2 %, additive %, PC1 score, AUC | https://scholarworks.uni.edu/grp/4669 |

## What you will have at the end

- [ ] **A public project page** on GitHub: https://github.com/mauricekuubata/greensand-nir (after you publish)
- [ ] **Library v1.0** (4,410 dry spectra) with its own DOI on Zenodo
- [ ] **Detection-limit benchmark and public leaderboard** with its own DOI
- [ ] **Moisture extension** (6,930 moist spectra) with its own DOI
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
