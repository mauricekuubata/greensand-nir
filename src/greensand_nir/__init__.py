"""greensand-nir: computed near-infrared spectra of foundry green sand, and tools to test calibrations on them.

Modules
-------
io            read USGS splib07 spectra, water optical constants, mixing rules
mixing        Hapke diffusive, linear and absorbance mixing; water film model
instrument    resample to an InGaAs instrument and add noise and packing effects
preprocess    absorbance, SNV, MSC, Savitzky-Golay, absorbance band area
compositions  library grid and random recipes
lab           recreate the Kuubata (2025) lab design, relative AUC and scaled PCA
calibrate     PLSR with cross-validation, classical LOD
benchmark     detection-limit scoring protocol and baseline methods
"""

__version__ = "1.0.0"

from . import benchmark, calibrate, compositions, instrument, io, lab, mixing, preprocess  # noqa: F401
