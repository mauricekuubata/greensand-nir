"""Recreate the Kuubata (2025) laboratory design and analysis on computed spectra.

Plain-language summary: the UNI study measured dry sand with 3, 6, 9 and 12%
DC2 bentonite, each with 0, 1, 3 and 5% seacoal or 0, 0.5, 1 and 2% red iron
oxide. It then ran PCA (centred and scaled, as R's prcomp with scale.=TRUE) and
computed a relative AUC: the trapezoid area of (sample absorbance minus the 0%
additive absorbance at the same DC2 level) over wavelength in nm. These
functions do exactly the same on computed spectra, so the two can be compared
like for like.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .compositions import ORDER
from .mixing import mix
from .preprocess import absorbance, trapezoid

DC2_LEVELS = (3, 6, 9, 12)
ADDITIVE_LEVELS = {"seacoal": (0, 1, 3, 5), "iron_oxide": (0, 0.5, 1, 2)}


def design(additive):
    rows = []
    for dc in DC2_LEVELS:
        for L in ADDITIVE_LEVELS[additive]:
            r = {"clay_pct": dc, "seacoal_pct": 0.0, "iron_oxide_pct": 0.0, "moisture_pct": 0.0}
            r[f"{additive}_pct"] = float(L)
            r["silica_sand_pct"] = 100.0 - dc - L
            rows.append(r)
    return pd.DataFrame(rows)


def simulate(E, instrument, additive, grains=None, model="hapke_diffusive", tier=None, rng=None):
    """Computed instrument-resolution reflectance for the lab design (16 rows)."""
    d = design(additive)
    m = d[[f"{c}_pct" for c in ORDER]].to_numpy(float) / 100.0
    gr = [(grains or E.grain_um)[o] for o in ORDER]
    if any(isinstance(x, str) for x in gr):
        raise ValueError("grain sizes still hold a placeholder such as 'lab_fit'; pass numeric grains "
                         "(for example the sizes in data/processed/lab_calibration.json)")
    R = mix(E.matrix(list(ORDER)), m, [E.density[o] for o in ORDER], gr, model=model)
    Ri = instrument.resample(R) if tier is None else instrument.measure(R, tier, rng)
    return d, Ri


def relative_auc(A, wl, dc2, additive_pct):
    """Kuubata (2025) Appendix C2: area of (A - A_baseline at same DC2) over wavelength (trapezoid)."""
    A = np.asarray(A, float)
    out = np.zeros(len(A))
    for dc in np.unique(dc2):
        idx = np.where(dc2 == dc)[0]
        base = idx[np.asarray(additive_pct)[idx] == 0]
        if len(base) != 1:
            raise ValueError(f"need exactly one baseline for DC2 {dc}")
        out[idx] = trapezoid(A[idx] - A[base[0]], wl, axis=1)
    return out


def pca_scaled(A, n=5):
    """PCA on centred, unit-variance columns (R prcomp(center=TRUE, scale.=TRUE)).

    Returns (explained variance percent, scores)."""
    X = np.asarray(A, float)
    X = (X - X.mean(axis=0)) / X.std(axis=0, ddof=1)
    U, S, Vt = np.linalg.svd(X, full_matrices=False)
    var = S ** 2 / np.sum(S ** 2) * 100
    scores = U * S
    # sign convention: PC1 increases with mean absorbance
    if np.corrcoef(scores[:, 0], np.asarray(A).mean(axis=1))[0, 1] < 0:
        scores[:, 0] *= -1
    return var[:n], scores[:, :n]


def lab_auc_table(E, instrument, grains=None, model="hapke_diffusive", tier=None, rng=None):
    """Relative AUC for the 24 additive-containing lab mixtures, in the lab table order."""
    out = []
    for add in ("seacoal", "iron_oxide"):
        d, Ri = simulate(E, instrument, add, grains, model, tier, rng)
        auc = relative_auc(absorbance(Ri), instrument.centers, d["clay_pct"].to_numpy(),
                           d[f"{add}_pct"].to_numpy())
        d = d.assign(additive=add, AUC=auc)
        out.append(d[d[f"{add}_pct"] > 0])
    return pd.concat(out, ignore_index=True)
