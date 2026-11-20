"""Mixture computation: how pure-material spectra combine into a green sand spectrum.

Plain-language summary: green sand is a powder of several materials. Its
spectrum is not a simple average of the ingredients, because small dark
particles block more light than their weight suggests. The default rule here
(Hapke diffusive mixing) works in "single-scattering albedo", the chance a
photon survives one encounter with a grain, which does mix linearly by each
material's share of grain cross-section area. Two simpler rules are provided
for comparison.

Models
------
hapke_diffusive
    R -> w via the Hapke diffusive-reflectance relation r0 = (1-g)/(1+g),
    g = sqrt(1-w); mix w by cross-section fraction f_i ~ m_i / (rho_i d_i);
    convert back. Suited to hemispherical (integrating sphere) measurements.
linear
    Mass-fraction weighted average of reflectance (areal or checkerboard mixing).
absorbance_linear
    Mass-fraction weighted average of log10(1/R) (Beer-Lambert style).

Water
-----
Moisture is a uniform film on every grain surface. Film thickness t follows from
mass balance: water volume / total grain surface area (surface ~ 6 m / (rho d)).
Each grain's albedo is multiplied by exp(-2 alpha t k), with alpha the absorption
coefficient of liquid water and k a path factor (1.0 = pure geometry).
"""

from __future__ import annotations

import numpy as np

MODELS = ("hapke_diffusive", "linear", "absorbance_linear")
WATER_DENSITY = 1.0


def reflectance_to_ssa(r):
    r = np.clip(np.asarray(r, float), 1e-6, 1 - 1e-9)
    g = (1.0 - r) / (1.0 + r)
    return 1.0 - g * g


def ssa_to_reflectance(w):
    w = np.clip(np.asarray(w, float), 0.0, 1.0)
    g = np.sqrt(1.0 - w)
    return (1.0 - g) / (1.0 + g)


def cross_section_fractions(mass_frac, density, grain_um):
    """Relative geometric cross-section of each component.

    mass_frac: (N, k) or (k,) mass fractions; density, grain_um: (k,).
    Returns array of same shape as mass_frac, rows summing to 1.
    """
    m = np.atleast_2d(np.asarray(mass_frac, float))
    a = m / (np.asarray(density, float) * np.asarray(grain_um, float))
    a = a / a.sum(axis=1, keepdims=True)
    return a if np.ndim(mass_frac) == 2 else a[0]


def film_thickness_um(mass_frac_dry, density, grain_um, moisture_pct):
    """Water film thickness (micrometres) for each mixture.

    mass_frac_dry: (N, k) dry mass fractions; moisture_pct: (N,) percent of wet mass.
    """
    m = np.atleast_2d(np.asarray(mass_frac_dry, float))
    mw = np.asarray(moisture_pct, float).reshape(-1)
    if mw.size == 1 and m.shape[0] > 1:
        mw = np.full(m.shape[0], mw[0])
    water_per_dry = mw / (100.0 - mw)                      # g water per g dry solids
    vol = water_per_dry / WATER_DENSITY                    # cm3 per g dry
    surf = (6.0 * m / (np.asarray(density) * np.asarray(grain_um))).sum(axis=1)  # cm3/um per g
    return vol / surf


def mix(endmember_matrix, mass_frac, density=None, grain_um=None, model="hapke_diffusive",
        moisture_pct=None, water_alpha=None, path_factor=1.0):
    """Compute mixture reflectance spectra.

    endmember_matrix: (k, n) reflectance of k pure components on n wavelengths.
    mass_frac: (N, k) or (k,) dry mass fractions (rows are normalised to 1).
    density, grain_um: (k,) needed for hapke_diffusive and for moisture.
    moisture_pct: optional (N,) or scalar, percent of wet mass; needs water_alpha (n,) in 1/um.
    Returns (N, n) reflectance (or (n,) if mass_frac was 1-D).
    """
    if model not in MODELS:
        raise ValueError(f"model must be one of {MODELS}")
    single = np.ndim(mass_frac) == 1
    m = np.atleast_2d(np.asarray(mass_frac, float))
    m = m / m.sum(axis=1, keepdims=True)
    E = np.asarray(endmember_matrix, float)
    if E.shape[0] != m.shape[1]:
        raise ValueError("endmember_matrix rows must match mass_frac columns")

    W = reflectance_to_ssa(E)                               # (k, n)
    wet = moisture_pct is not None and np.any(np.asarray(moisture_pct) > 0)
    if wet:
        if water_alpha is None or density is None or grain_um is None:
            raise ValueError("moisture needs water_alpha, density and grain_um")
        t = film_thickness_um(m, density, grain_um, moisture_pct)       # (N,)
        trans = np.exp(-2.0 * path_factor * t[:, None] * np.asarray(water_alpha)[None, :])  # (N, n)

    if model == "hapke_diffusive":
        f = cross_section_fractions(m, density, grain_um)               # (N, k)
        if wet:
            out = ssa_to_reflectance((f @ W) * trans)
        else:
            out = ssa_to_reflectance(f @ W)
    else:
        if wet:
            # per-mixture wet endmembers, then the simple rule
            Ew = ssa_to_reflectance(W[None, :, :] * trans[:, None, :])  # (N, k, n)
            if model == "linear":
                out = np.einsum("nk,nkj->nj", m, Ew)
            else:
                out = 10 ** (-np.einsum("nk,nkj->nj", m, np.log10(1 / Ew)))
        else:
            if model == "linear":
                out = m @ E
            else:
                out = 10 ** (-(m @ np.log10(1 / np.clip(E, 1e-6, None))))
    return out[0] if single else out


def fit_grain_ratio(mix_measured, r_a, r_b, mass_frac_a, density_a, density_b, grain_b_um,
                    wl=None, band=None, grid=None):
    """Fit the effective grain size of component a from a measured two-component mixture.

    Returns (best_grain_a_um, rmse, curve) where curve is (grid, rmse) for inspection.
    """
    if grid is None:
        grid = np.geomspace(0.05, 500, 400)
    sel = np.ones_like(mix_measured, bool) if band is None else (wl >= band[0]) & (wl <= band[1])
    E = np.vstack([r_a, r_b])
    m = np.array([mass_frac_a, 1 - mass_frac_a])
    errs = []
    for g in grid:
        pred = mix(E, m, [density_a, density_b], [g, grain_b_um])
        errs.append(np.sqrt(np.mean((pred[sel] - mix_measured[sel]) ** 2)))
    errs = np.array(errs)
    i = int(np.argmin(errs))
    return float(grid[i]), float(errs[i]), (grid, errs)
