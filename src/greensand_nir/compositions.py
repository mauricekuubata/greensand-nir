"""Mixture recipes: the grid of compositions in the library and random samples for the benchmark.

Plain-language summary: a "composition" is one recipe, such as 8% clay, 1.5%
seacoal, 0.4% iron oxide, rest silica sand. These functions list every recipe
in the library grid and draw random recipes for testing.
"""

from __future__ import annotations

import itertools

import numpy as np
import pandas as pd

ADDITIVES = ("clay", "seacoal", "iron_oxide")
ORDER = ("silica_sand", "clay", "seacoal", "iron_oxide")


def _levels(spec):
    n = int(round((spec["stop"] - spec["start"]) / spec["step"])) + 1
    return np.round(spec["start"] + spec["step"] * np.arange(n), 6)


def grid(grid_spec: dict) -> pd.DataFrame:
    """Full-factorial grid from a {column_pct: {start, stop, step}} block of the rules."""
    cols = list(grid_spec.keys())
    rows = list(itertools.product(*[_levels(grid_spec[c]) for c in cols]))
    df = pd.DataFrame(rows, columns=cols)
    if "moisture_pct" not in df:
        df["moisture_pct"] = 0.0
    df["silica_sand_pct"] = np.round(100.0 - df["clay_pct"] - df["seacoal_pct"] - df["iron_oxide_pct"], 6)
    return df[["silica_sand_pct", "clay_pct", "seacoal_pct", "iron_oxide_pct", "moisture_pct"]]


def mass_fractions(df: pd.DataFrame, order=ORDER) -> np.ndarray:
    """Dry mass fractions (N, k) in component order."""
    return df[[f"{c}_pct" for c in order]].to_numpy(float) / 100.0


def random_compositions(n, rng, clay=(3, 12), seacoal=(0, 5), iron_oxide=(0, 2), moisture=(0, 0),
                        fixed=None):
    """Uniform random recipes within production ranges; 'fixed' pins a column, e.g. {'seacoal_pct': 0.5}."""
    rng = np.random.default_rng(rng)
    df = pd.DataFrame({
        "clay_pct": rng.uniform(*clay, n),
        "seacoal_pct": rng.uniform(*seacoal, n),
        "iron_oxide_pct": rng.uniform(*iron_oxide, n),
        "moisture_pct": rng.uniform(*moisture, n) if moisture[1] > moisture[0] else np.full(n, float(moisture[0])),
    })
    for k, v in (fixed or {}).items():
        df[k] = v
    df["silica_sand_pct"] = 100.0 - df["clay_pct"] - df["seacoal_pct"] - df["iron_oxide_pct"]
    return df[["silica_sand_pct", "clay_pct", "seacoal_pct", "iron_oxide_pct", "moisture_pct"]]
