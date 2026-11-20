"""Instrument simulation: resample to a 1000-2350 nm InGaAs instrument and add realistic noise.

Plain-language summary: the computed spectra are perfectly smooth and finely
spaced. A real handheld or benchtop NIR instrument sees fewer, wider channels
and adds random noise, plus small shifts from how tightly the sand is packed.
These functions add those effects so methods are tested under real conditions.
"""

from __future__ import annotations

import numpy as np

FWHM_TO_SIGMA = 1.0 / (2.0 * np.sqrt(2.0 * np.log(2.0)))


def channel_centers(start_nm=1000, stop_nm=2350, step_nm=6):
    n = int(np.floor((stop_nm - start_nm) / step_nm + 1e-9)) + 1
    return start_nm + step_nm * np.arange(n, dtype=float)


def srf_matrix(wl_native, centers, fwhm_nm):
    """Gaussian spectral response matrix (channels x native wavelengths), rows sum to 1.

    Edge channels are renormalised over the part of the response inside the native grid.
    """
    s = fwhm_nm * FWHM_TO_SIGMA
    M = np.exp(-0.5 * ((wl_native[None, :] - centers[:, None]) / s) ** 2)
    return M / M.sum(axis=1, keepdims=True)


def resample(R, wl_native, centers, fwhm_nm):
    M = srf_matrix(wl_native, centers, fwhm_nm)
    return np.asarray(R) @ M.T


def snr_profile(centers, nm, factor):
    return np.interp(centers, nm, factor)


def add_noise(R, centers, snr, multiplicative_sd=0.0, offset_sd=0.0, slope_sd=0.0,
              profile_nm=None, profile_factor=None, rng=None):
    """Add instrument noise and packing (scatter) effects.

    R: (N, c) reflectance on instrument channels.
    snr: signal-to-noise ratio for a 100 percent reflector at the best channels;
         white noise sd per channel = 1 / (snr * profile(lambda)).
    multiplicative_sd, offset_sd, slope_sd: per-spectrum random gain, offset and
         linear baseline tilt (tilt expressed as reflectance change across the range).
    """
    rng = np.random.default_rng(rng)
    R = np.atleast_2d(np.asarray(R, float))
    N, c = R.shape
    prof = np.ones(c) if profile_nm is None else snr_profile(centers, profile_nm, profile_factor)
    x = (centers - centers.mean()) / (centers.max() - centers.min())
    gain = 1.0 + rng.normal(0, multiplicative_sd, (N, 1)) if multiplicative_sd else 1.0
    off = rng.normal(0, offset_sd, (N, 1)) if offset_sd else 0.0
    tilt = rng.normal(0, slope_sd, (N, 1)) * x[None, :] if slope_sd else 0.0
    noise = rng.normal(0, 1, (N, c)) / (snr * prof[None, :])
    return np.clip(R * gain + off + tilt + noise, 1e-4, 1.5)


class Instrument:
    """Convenience wrapper built from the 'instrument' and 'noise_tiers' blocks of the rules."""

    def __init__(self, rules, wl_native):
        ins = rules["instrument"]
        self.centers = channel_centers(ins["start_nm"], ins["stop_nm"], ins["step_nm"])
        self.fwhm = ins["fwhm_nm"]
        self.M = srf_matrix(wl_native, self.centers, self.fwhm)
        self.tiers = rules["noise_tiers"]
        p = rules.get("noise_snr_profile", {})
        self.pnm, self.pf = p.get("nm"), p.get("factor")

    def resample(self, R):
        return np.asarray(R) @ self.M.T

    def measure(self, R_native, tier="lab", rng=None):
        t = self.tiers[tier]
        return add_noise(self.resample(R_native), self.centers, t["snr"], t["multiplicative_sd"],
                         t["offset_sd"], t["slope_sd"], self.pnm, self.pf, rng)
