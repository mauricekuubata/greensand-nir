# Laboratory reference values (Kuubata 2025)

Plain-language summary: these are the measured results from Maurice Kuubata's UNI
graduate study, typed in from the data tables printed in its Appendix D. The computed
library is checked and calibrated against them. **Every value here was transcribed by
hand from a printed image and must be checked by the author against the original
spreadsheets ("Seacoal Book1.xlsx", "Seacoal_PC1_AUC.xlsx" and the red iron oxide
equivalents) before release.**

Source: Kuubata, M. (2025). *NIR Spectroscopy as a Tool for Identifying Additives in
Foundry Green Sands.* Graduate Research Paper, University of Northern Iowa.
https://scholarworks.uni.edu/grp/4669 . Appendix D, snippets D2 (seacoal) and D4
(red iron oxide).

Columns: `PC1` is the first principal component score from the paper's R code
(prcomp, centred and scaled, 1000-2350 nm, one PCA per additive series). `AUC` is the
trapezoid area of (sample absorbance minus the 0% additive absorbance at the same DC2
level) over wavelength in nm. `A_999.695nm` is the measured absorbance in the first
detector pixel (AvaSoft absorbance, mirror reference).

Instrument: Avantes AvaSpec-NIR256-2.5TEC with AvaSphere-50-LS-HAL-12V, 1000-2350 nm,
5 ms integration, 100 scans averaged, detector -8 C. Dry samples in a petri dish.
