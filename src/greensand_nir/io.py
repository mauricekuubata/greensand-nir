"""Reading the USGS splib07 ASCII files, the water optical constants, and the mixing rules.

Plain-language summary: these functions open the raw public files and turn them
into arrays of numbers the rest of the package can use.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

import numpy as np

SPLIB_NODATA = -1.0e30  # splib07 marks deleted channels with -1.23e34


def read_splib(path: str) -> np.ndarray:
    """Read one splib07 ASCII spectrum (one header line, one value per channel).

    Deleted channels (value -1.23e34) are returned as NaN.
    """
    vals = np.loadtxt(path, skiprows=1, dtype=float)
    vals[vals < SPLIB_NODATA] = np.nan
    return vals


def read_wavelengths_nm(path: str) -> np.ndarray:
    """Read a splib07 wavelength file (micrometres) and return nanometres."""
    return read_splib(path) * 1000.0


def read_water_alpha(path: str, wl_nm: np.ndarray) -> np.ndarray:
    """Absorption coefficient of liquid water (1/um) on the wavelength grid.

    Reads a refractiveindex.info YAML file with tabulated 'wavelength_um n k'
    rows and returns alpha = 4 pi k / lambda, interpolated in log-k space.
    """
    rows = []
    in_data = False
    with open(path, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("data:"):
                in_data = True
                continue
            if in_data:
                parts = s.split()
                if len(parts) != 3:
                    if rows:
                        break
                    continue
                try:
                    rows.append([float(p) for p in parts])
                except ValueError:
                    break
    arr = np.array(rows)
    lam_um, k = arr[:, 0], arr[:, 2]
    x = wl_nm / 1000.0
    logk = np.interp(x, lam_um, np.log(k))
    return 4.0 * np.pi * np.exp(logk) / x


def load_rules(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class Endmembers:
    """Reference spectra on the native 1 nm grid, restricted to the working range."""

    wl: np.ndarray
    spectra: dict  # component name -> reflectance array
    density: dict
    grain_um: dict
    labels: dict
    files: dict
    water_alpha: np.ndarray | None = None
    extra: dict = field(default_factory=dict)  # validation and alternative spectra by file name

    @property
    def names(self):
        return list(self.spectra.keys())

    def matrix(self, order=None) -> np.ndarray:
        order = order or self.names
        return np.vstack([self.spectra[n] for n in order])


def load_endmembers(rules: dict, raw_dir: str, overrides: dict | None = None) -> Endmembers:
    """Load the component spectra named in the rules file.

    overrides: optional {component: file name} to swap in an alternative spectrum,
    or {component: {"grain_um": x}} to change a property, for sensitivity runs.
    """
    overrides = overrides or {}
    wl_all = read_wavelengths_nm(os.path.join(raw_dir, rules["wavelength_file"]))
    lo, hi = rules["native_range_nm"]
    keep = (wl_all >= lo - 0.01) & (wl_all <= hi + 0.01)
    wl = np.round(wl_all[keep], 3)

    spectra, density, grain, labels, files = {}, {}, {}, {}, {}
    for name, comp in rules["components"].items():
        ov = overrides.get(name, {})
        if isinstance(ov, str):
            ov = {"spectrum": ov}
        fname = ov.get("spectrum", comp["spectrum"])
        r = read_splib(os.path.join(raw_dir, fname))[keep]
        if np.isnan(r).any():
            raise ValueError(f"{fname} has deleted channels inside {lo}-{hi} nm")
        spectra[name] = r
        density[name] = float(ov.get("density", comp["density"]))
        g = ov.get("grain_um", comp["grain_um"])
        grain[name] = g if isinstance(g, str) else float(g)
        labels[name] = comp.get("label", name)
        files[name] = fname

    extra = {}
    for fname in rules.get("validation_spectra", {}).values():
        p = os.path.join(raw_dir, fname)
        if os.path.exists(p):
            extra[fname] = read_splib(p)[keep]

    alpha = None
    wfile = rules.get("water", {}).get("optical_constants")
    if wfile and os.path.exists(os.path.join(raw_dir, wfile)):
        alpha = read_water_alpha(os.path.join(raw_dir, wfile), wl)

    return Endmembers(wl, spectra, density, grain, labels, files, alpha, extra)
