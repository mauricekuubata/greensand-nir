# Talking about the Green Sand Near-Infrared Reference Library

## 60-second version

**The problem:** foundries still control green sand with slow offline tests like loss on ignition, so a bad batch of sand can reach the mold line before the result comes back, and the problem shows up later as scrap castings.

**What I built:** an open reference library of 11,340 computed near-infrared spectra of green sand, covering the clay, seacoal, iron oxide and moisture ranges used in production. It is calibrated against my own laboratory measurements from my graduate study at UNI. I also built a fixed benchmark that measures the smallest amount of an additive any NIR method can detect, and an open Python package to reproduce it.

**What it shows:** with laboratory-grade noise, standard partial least squares regression detects seacoal from about 0.5 percent and red iron oxide from about 0.1 percent in dry sand. At plant-floor noise, those figures are 0.75 and 0.15 percent.

**Who can use it:** foundries choosing a sand sensor, sensor makers testing calibrations, and researchers comparing methods on the same public test.

**Where it is:** github.com/mauricekuubata/greensand-nir, archived on Zenodo with DOIs.

## Two-sentence version

Maurice Kuubata built the first open near-infrared reference library and detection-limit benchmark for foundry green sand, calibrated against his own UNI laboratory measurements. It tells foundries and sensor makers which seacoal and iron oxide levels an NIR sensor can actually detect, so sand can be checked before pouring instead of after scrap.

## Questions you may be asked

1. **Where does the data come from?** Measured spectra of pure minerals from the U.S. Geological Survey's public spectral library, mixed with a standard physics model, and calibrated against 24 dry green sand mixtures I measured at UNI.
2. **What are its limits?** The spectra are computed, not measured, and calibrated to one small dry laboratory study. The USGS library has no coal, so seacoal uses a stand-in, and the moisture model is a first approximation. The numbers show what is detectable in principle, not what a specific sensor will do in a specific plant.
3. **Why does this matter for the United States?** The Department of Defense's February 2022 supply-chain report names castings and forgings among its high-priority areas. Better, faster sand control means less scrap and steadier output from U.S. foundries, and this gives the whole industry a free, common yardstick for NIR sensors.
