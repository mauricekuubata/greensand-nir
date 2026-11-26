"""Tests for greensand-nir. Run with: pytest

Plain-language summary: these automatic checks confirm the maths behaves as it
should (for example, a mixture of one material equals that material, darker
ingredients darken the mix, and the scoring rule gives the expected answer on
a made-up example).
"""

import os

import numpy as np
import pandas as pd
import pytest

import greensand_nir as g

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "data", "raw", "splib07_selected")
HAVE_DATA = os.path.exists(os.path.join(RAW, "s07_ASD_Kerogen_BK-Cornell_BECKa_AREF.txt"))


def test_ssa_roundtrip():
    r = np.linspace(0.01, 0.95, 50)
    assert np.allclose(g.mixing.ssa_to_reflectance(g.mixing.reflectance_to_ssa(r)), r, atol=1e-9)


@pytest.mark.parametrize("model", g.mixing.MODELS)
def test_pure_component_returns_itself(model):
    E = np.array([[0.6, 0.5, 0.4], [0.05, 0.05, 0.06]])
    out = g.mixing.mix(E, [1.0, 0.0], [2.65, 1.3], [250, 40], model=model)
    assert np.allclose(out, E[0], atol=1e-6)


def test_dark_component_darkens_more_under_hapke_than_linear():
    E = np.array([[0.6, 0.6], [0.04, 0.04]])
    m = [0.97, 0.03]
    h = g.mixing.mix(E, m, [2.65, 1.3], [250, 40])
    lin = g.mixing.mix(E, m, model="linear")
    assert np.all(h < lin)


def test_monotone_in_absorber():
    E = np.array([[0.6, 0.6], [0.04, 0.04]])
    vals = [g.mixing.mix(E, [1 - x, x], [2.65, 1.3], [250, 40])[0] for x in (0, 0.01, 0.02, 0.05)]
    assert np.all(np.diff(vals) < 0)


def test_cross_section_fractions_sum_to_one():
    f = g.mixing.cross_section_fractions(np.array([[0.9, 0.08, 0.02]]), [2.65, 2.35, 1.3], [250, 10, 40])
    assert np.isclose(f.sum(), 1.0)


def test_water_darkens_at_1940_more_than_1100():
    wl = np.array([1100.0, 1940.0])
    alpha = np.array([0.0001, 0.012])
    E = np.array([[0.6, 0.6], [0.7, 0.7]])
    dry = g.mixing.mix(E, [0.92, 0.08], [2.65, 2.35], [250, 10])
    wet = g.mixing.mix(E, [0.92, 0.08], [2.65, 2.35], [250, 10], moisture_pct=4.0, water_alpha=alpha)
    drop = dry - wet
    assert drop[1] > drop[0] > -1e-12


def test_film_thickness_scales_with_moisture():
    m = np.array([[0.9, 0.1]])
    t2 = g.mixing.film_thickness_um(m, [2.65, 2.35], [250, 10], 2.0)[0]
    t4 = g.mixing.film_thickness_um(m, [2.65, 2.35], [250, 10], 4.0)[0]
    assert 1.9 < t4 / t2 < 2.2


def test_srf_rows_sum_to_one_and_channels():
    wl = np.arange(1000, 2351, 1.0)
    c = g.instrument.channel_centers(1000, 2350, 6.93)
    M = g.instrument.srf_matrix(wl, c, 15)
    assert np.allclose(M.sum(axis=1), 1)
    assert len(c) == 195


def test_noise_reproducible_and_scaled():
    c = g.instrument.channel_centers(1000, 2350, 6.93)
    R = np.full((200, len(c)), 0.5)
    a = g.instrument.add_noise(R, c, snr=1000, rng=1)
    b = g.instrument.add_noise(R, c, snr=1000, rng=1)
    assert np.array_equal(a, b)
    assert abs(np.std(a - 0.5) - 1e-3) < 2e-4


def test_score_levels_perfect_separation():
    lv = np.r_[np.zeros(100), np.full(50, 0.1), np.full(50, 0.5)]
    s = lv + np.r_[np.random.default_rng(0).normal(0, 0.01, 100), np.zeros(100)]
    tab, lod, thr = g.benchmark.score_levels(s, lv)
    assert lod == 0.1


def test_score_levels_requires_higher_levels_to_pass():
    lv = np.r_[np.zeros(100), np.full(50, 0.1), np.full(50, 0.5)]
    s = np.r_[np.random.default_rng(0).normal(0, 0.01, 100), np.ones(50), np.zeros(50) - 1]
    tab, lod, thr, det = g.benchmark.score_levels(s, lv, details=True)
    assert np.isnan(lod) and det["lowest_level_detected"] == 0.1 and det["misses_higher_levels"]


def test_score_levels_ties():
    lv = np.r_[np.zeros(100), np.full(100, 1.0)]
    s = np.r_[np.r_[np.zeros(90), np.ones(10)], np.ones(100)]  # 10% of blanks tied at 1.0
    tab, lod, thr = g.benchmark.score_levels(s, lv)
    assert np.isclose(tab.power.iloc[0], 0.5)  # weight 0.5 keeps false alarms at exactly 5%


def test_relative_auc_zero_for_baseline():
    wl = np.linspace(1000, 2350, 10)
    A = np.vstack([np.full(10, 0.1), np.full(10, 0.2)])
    auc = g.lab.relative_auc(A, wl, np.array([3, 3]), np.array([0, 1]))
    assert auc[0] == 0 and np.isclose(auc[1], 0.1 * 1350)


def test_plsr_recovers_linear_signal():
    rng = np.random.default_rng(0)
    y = rng.uniform(0, 5, 200)
    X = np.outer(y, np.linspace(1, 2, 30)) + rng.normal(0, 0.01, (200, 30))
    r = g.calibrate.fit_plsr(X, y, 5)
    assert r["r2cv"] > 0.99


def test_grid_counts():
    df = g.compositions.grid({"clay_pct": {"start": 3, "stop": 12, "step": 1},
                              "seacoal_pct": {"start": 0, "stop": 5, "step": 0.25},
                              "iron_oxide_pct": {"start": 0, "stop": 2, "step": 0.1}})
    assert len(df) == 10 * 21 * 21
    assert np.allclose(df[["silica_sand_pct", "clay_pct", "seacoal_pct", "iron_oxide_pct"]].sum(axis=1), 100)


@pytest.mark.skipif(not HAVE_DATA, reason="run code/01_fetch.py first")
def test_endmembers_load_and_values():
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    E = g.io.load_endmembers(rules, RAW)
    assert len(E.wl) == 1351 and E.wl[0] == 1000 and E.wl[-1] == 2350
    i = int(np.argmin(abs(E.wl - 1700)))
    assert abs(E.spectra["silica_sand"][i] - 0.64859) < 1e-4
    assert E.water_alpha is not None and E.water_alpha[int(np.argmin(abs(E.wl - 1940)))] > 0.01


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_compositions.csv")),
                    reason="run the pipeline first")
def test_library_files_consistent():
    comp = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_compositions.csv"))
    inst = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_spectra_instrument.csv"))
    assert len(comp) == len(inst) == 4410
    assert (comp.sample_id == inst.sample_id).all()


def test_band_area_uses_trapezoid_rule():
    wl = np.array([1000.0, 1500.0, 2000.0])
    R = np.full((1, 3), 0.1)  # absorbance 1 everywhere
    assert np.isclose(g.preprocess.band_area(R, wl, 1000, 2000)[0], 1000.0)


def test_simulate_rejects_placeholder_grain_sizes():
    class _E:
        grain_um = {"silica_sand": 250.0, "clay": 10.0, "seacoal": "lab_fit", "iron_oxide": 2.5}
    with pytest.raises(ValueError):
        g.lab.simulate(_E(), None, "seacoal")


@pytest.mark.skipif(not os.path.exists(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_spectra_instrument.csv")),
                    reason="run the pipeline first")
def test_instrument_columns_match_channel_centres():
    rules = g.io.load_rules(os.path.join(ROOT, "config", "mixing_rules.json"))
    ins = rules["instrument"]
    centres = g.instrument.channel_centers(ins["start_nm"], ins["stop_nm"], ins["step_nm"])
    cols = pd.read_csv(os.path.join(ROOT, "library", "v1.0", "GSNIR-v1.0_spectra_instrument.csv"), nrows=0).columns[1:]
    assert np.allclose([float(c[2:]) for c in cols], centres, atol=0.005)
