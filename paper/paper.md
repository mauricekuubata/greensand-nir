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
date: 26 November 2026
bibliography: paper.bib
---

# Summary

Foundry green sand is silica sand bonded with bentonite clay and water, usually with a carbonaceous additive such as seacoal and, in some systems, red iron oxide. Foundries still check additive levels with slow offline tests such as loss on ignition, so out-of-specification sand can reach the molding line before a result comes back. Near-infrared (NIR) spectroscopy reads a sample in seconds, and laboratory work has shown that it separates seacoal and red iron oxide in dry green sand [@kuubata2025]. `greensand-nir` is an open Python package that computes realistic NIR spectra of green sand mixtures from public reference spectra, simulates how a typical NIR instrument would read them, and scores any calibration method on a fixed detection-limit test, so that people choosing or building an NIR method for sand control can compare methods on common ground.

# Statement of need

Anyone evaluating NIR for green sand control currently has to collect and measure their own mixtures before they can say which additive levels a method detects, and published studies use different samples, instruments and decision rules, so their figures cannot be compared directly. `greensand-nir` provides the missing common reference: (1) a mixing engine that computes green sand reflectance from USGS Spectral Library Version 7 spectra [@kokaly2017] using Hapke single-scattering-albedo mixing [@hapke2012], with an optional grain-surface water film based on liquid water optical constants [@segelstein1981]; (2) an instrument model for the 1000-2350 nm InGaAs class, with signal-to-noise and packing (gain, offset, tilt) effects; (3) standard NIR preprocessing and partial least squares regression (PLSR) calibration [@wold2001]; (4) a calibration of the two least-known inputs, the effective particle sizes of seacoal and red iron oxide, against 24 measured dry laboratory mixtures; and (5) a benchmark that turns any method's scores into a detection limit under one stated rule. The intended users are foundry engineers and sand laboratories evaluating NIR, sensor makers testing calibrations, and chemometrics researchers who need a domain test set.

# State of the field

General-purpose tools cover parts of this workflow. scikit-learn [@pedregosa2011] provides PLSR and the classifiers used as baselines, and `greensand-nir` builds on it rather than reimplementing them. Spectral Python [@spy] reads and processes spectral libraries and imagery, and USGS splib07 [@kokaly2017] supplies measured spectra of pure minerals and materials, but neither models foundry mixtures. Hapke mixing is widely used in planetary and mineral remote sensing, usually in project-specific code [@hapke2012]. We are not aware of an open package, dataset or benchmark aimed at foundry green sand. The domain layer here (green sand composition model, laboratory-calibrated stand-in materials, instrument model for the InGaAs class used in foundry studies, and a detection-limit scoring rule) does not belong inside a general library, so a separate package that depends on those libraries was the appropriate choice.

# Software design

All modelling assumptions live in one rules file (`config/mixing_rules.json`), and numbered pipeline scripts read it and rebuild every output, so a changed assumption propagates to the library, benchmark, figures and documents. Hapke diffusive mixing was chosen over simple averaging because dark, fine particles darken a powder far more than their mass share suggests; on a measured USGS mixture of 2% hematite and 98% quartz, the Hapke model fits with root-mean-square error 0.0112 against 0.0222 for linear mixing. The trade-off is that Hapke theory is approximate for particles smaller than the wavelength, so the fitted effective sizes are treated as empirical parameters and their stability is reported (leave-one-group-out refits). The benchmark scores a method by its output scores only: the alarm threshold is set at a 5% false-alarm rate on clean samples (with randomised tie handling), and the detection limit is the lowest level detected in at least 95% of samples at that level and every level above it. Any method, including non-linear classifiers, can therefore be compared without access to its internals. Random seeds are fixed, so the pipeline reproduces its outputs exactly, and every number in the documentation is written from a generated statistics file rather than typed by hand.

# Research impact statement

The package is new and has no external users yet. Its near-term value rests on concrete, reproducible materials: a library of 4,410 dry and 6,930 moist computed spectra, 12 benchmark sets (dry and moist sand, three noise tiers, two additives) with baseline results for five methods, a public leaderboard with a submission script, and 20 automated tests. The computed spectra reproduce 5/5 laboratory trends tested in [@kuubata2025]. All outputs are archived on Zenodo with DOIs, and the stated next step is replacing the stand-in materials with measured spectra of foundry materials.

# AI usage disclosure

Claude (Anthropic) was used to write and review code, tests and documentation and to draft this paper. The author set every mixing rule and modelling assumption, checked the computed results against his own laboratory measurements, verified reference values, worked examples and library rows by hand using the project's verification checklist, and revised this paper.

# Acknowledgements

Reference spectra are from the U.S. Geological Survey Spectroscopy Laboratory. This work received no specific funding.

# References
