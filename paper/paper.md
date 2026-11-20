---
title: 'greensand-nir: an open Python package and reference library for near-infrared control of foundry green sand additives'
tags:
  - Python
  - near-infrared spectroscopy
  - foundry
  - chemometrics
  - spectral mixing
authors:
  - name: Maurice Kuubata
    orcid: 0009-0003-3178-5971
    affiliation: 1
affiliations:
  - name: Independent Researcher, Dubuque, Iowa, USA
    index: 1
date: 20 November 2026
bibliography: paper.bib
---

# Summary

Foundry green sand is silica sand bonded with bentonite clay and water, with carbonaceous additives such as seacoal and, in some systems, red iron oxide. Its additive levels are still controlled with slow offline tests such as loss on ignition, so out-of-specification sand can reach molding before results return. Near-infrared (NIR) spectroscopy can read sand in seconds, and laboratory work has shown that it separates seacoal and red iron oxide in dry green sand [@kuubata2025]. What has been missing is an open, common reference: which additive levels can an NIR method actually detect, and how does a new calibration compare?

`greensand-nir` provides (1) a mixing engine that computes green sand reflectance spectra from USGS Spectral Library Version 7 reference spectra [@kokaly2017] using Hapke single-scattering-albedo mixing [@hapke2012], with a grain-surface water film using liquid water optical constants [@segelstein1981]; (2) an instrument model for the 1000-2350 nm InGaAs class, with noise and packing effects; (3) standard NIR preprocessing and PLSR calibration [@wold2001]; (4) a library of 4,410 dry and 6,930 moist computed spectra; and (5) a detection-limit benchmark with a fixed scoring rule and baselines.

# Statement of need

Chemometric NIR studies of foundry sand have used proprietary spectra and instrument-specific calibrations, so detection limits are rarely reported and never comparable. Spectral libraries such as USGS splib07 hold pure minerals, not foundry mixtures. `greensand-nir` turns those public spectra into foundry-relevant mixtures, calibrates the two least-known inputs (effective particle sizes of seacoal and red iron oxide) against measured laboratory mixtures, and reports the result as detection limits under one public rule. Calibrated to 24 measured dry mixtures, the computed spectra reproduce 5/5 laboratory trends tested, including first-principal-component dominance (99.78% computed vs 99.23% measured for seacoal). Baseline PLSR detects seacoal from 0.5% and red iron oxide from 0.1% at laboratory-grade noise.

# Functionality

See the README for a worked example. Core modules: `mixing` (Hapke diffusive, linear and absorbance mixing; water film), `instrument` (Gaussian spectral response, signal-to-noise profile, gain, offset and tilt), `preprocess`, `calibrate` (PLSR with cross-validated component selection), `lab` (replication of a published laboratory analysis), and `benchmark` (scoring rule and baselines).

# Acknowledgements

Spectra from the U.S. Geological Survey Spectroscopy Laboratory. Claude (Anthropic) assisted with code and data handling; the author set every mixing rule and verified every output.

# References
