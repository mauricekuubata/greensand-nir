"""Standard NIR preprocessing.

Plain-language summary: before a calibration model sees a spectrum, it is
usually converted to absorbance and corrected for packing and baseline effects.
These are the common, well-documented corrections.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import savgol_filter

# numpy >= 2.0 names the trapezoid rule np.trapezoid; older releases call it np.trapz
trapezoid = getattr(np, "trapezoid", None) or np.trapz


def absorbance(R):
    """log10(1/R)."""
    return -np.log10(np.clip(np.asarray(R, float), 1e-6, None))


def snv(X):
    """Standard normal variate: centre and scale each spectrum by its own mean and sd."""
    X = np.asarray(X, float)
    return (X - X.mean(axis=1, keepdims=True)) / X.std(axis=1, keepdims=True)


def msc(X, reference=None):
    """Multiplicative scatter correction against the mean (or a given reference) spectrum."""
    X = np.asarray(X, float)
    ref = X.mean(axis=0) if reference is None else np.asarray(reference, float)
    out = np.empty_like(X)
    for i, x in enumerate(X):
        b, a = np.polyfit(ref, x, 1)
        out[i] = (x - a) / b
    return out


def savgol(X, window=11, poly=2, deriv=1):
    """Savitzky-Golay smoothing or derivative along wavelength."""
    return savgol_filter(np.asarray(X, float), window, poly, deriv=deriv, axis=1)


def pipeline(R, steps=("absorbance", "snv")):
    """Apply named steps in order: absorbance, snv, msc, sg1 (first derivative), sg2."""
    X = np.asarray(R, float)
    for s in steps:
        if s == "absorbance":
            X = absorbance(X)
        elif s == "snv":
            X = snv(X)
        elif s == "msc":
            X = msc(X)
        elif s == "sg1":
            X = savgol(X, deriv=1)
        elif s == "sg2":
            X = savgol(X, deriv=2)
        else:
            raise ValueError(f"unknown step {s}")
    return X


def band_area(R, wl, lo=1000, hi=2350):
    """Area under the absorbance curve between lo and hi nm (absorbance x nm)."""
    sel = (wl >= lo) & (wl <= hi)
    A = absorbance(R)
    return trapezoid(A[..., sel], wl[sel], axis=-1)
