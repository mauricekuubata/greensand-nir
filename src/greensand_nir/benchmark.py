"""Detection-limit benchmark: scoring rule and baseline methods.

Plain-language summary: a method "detects" an additive level if it can tell
sand containing that level apart from sand with none of it, reliably. Here
"reliably" means: set the alarm so that at most 5 percent of clean (zero-level)
samples trigger it, then check that at least 95 percent of samples at the test
level do trigger it. The detection limit is the lowest level where this holds,
and keeps holding at every higher level. Every method, including anyone's new
method, is scored by exactly this rule, so results are comparable.

Scoring protocol (all methods)
------------------------------
1. Train on the calibration set (spectra plus known compositions).
2. Output one score per test spectrum: higher means more of the target additive.
3. Threshold = 95th percentile of scores on the test blanks (false alarm rate 5%).
   Ties at the threshold (common for classifier probabilities of exactly 1.0) are
   handled the standard way: samples tied with the threshold count with the weight
   that makes the false-alarm rate on blanks exactly 5% (randomised Neyman-Pearson test).
4. Power at level L = share of test spectra at L scoring above the threshold (plus tied share x weight).
5. Detection limit = lowest L with power >= 0.95 at L and every level above it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from .calibrate import fit_plsr
from .preprocess import pipeline

ALPHA = 0.05
POWER = 0.95

LEVELS = {
    "seacoal": [0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0],
    "iron_oxide": [0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 0.75, 1.0, 1.5, 2.0],
}


def score_levels(scores, levels, alpha=ALPHA, power=POWER, details=False):
    """Apply the scoring protocol.

    scores: array of method scores for the test set; levels: matching true target levels
    (0 for blanks). Returns (per-level DataFrame, detection limit or NaN, threshold).
    With details=True also returns a dict with 'lowest_level_detected' (first level with
    power >= 0.95, even if a higher level later fails) and 'misses_higher_levels'.
    """
    scores = np.asarray(scores, float)
    levels = np.round(np.asarray(levels, float), 6)
    blank = scores[levels == 0]
    thr = float(np.quantile(blank, 1 - alpha))
    above, tied = np.mean(blank > thr), np.mean(blank == thr)
    q = float(np.clip((alpha - above) / tied, 0, 1)) if tied > 0 else 0.0
    rows = []
    for L in sorted(set(levels[levels > 0])):
        s = scores[levels == L]
        rows.append({"level": L, "n": len(s), "power": float(np.mean(s > thr) + q * np.mean(s == thr)),
                     "median_score": float(np.median(s))})
    tab = pd.DataFrame(rows)
    ok = (tab["power"] >= power).to_numpy()
    lod = np.nan
    for i in range(len(ok)):
        if ok[i:].all():
            lod = float(tab["level"].iloc[i])
            break
    if details:
        first = float(tab["level"][ok].iloc[0]) if ok.any() else np.nan
        miss = bool(ok.any() and not ok[int(np.argmax(ok)):].all())
        return tab, lod, thr, {"lowest_level_detected": first, "misses_higher_levels": miss}
    return tab, lod, thr


# --------------------------------------------------------------------- baselines
# Each baseline: fit(R_train, y_train) -> object with .score(R_test) -> 1-D scores.

class _PCA_LDA:
    """Principal component analysis on absorbance, then linear discriminant (blank vs present)."""
    name = "PCA-LDA"

    def __init__(self, n_components=10):
        self.k = n_components

    def fit(self, R, y):
        X = pipeline(R, ("absorbance",))
        self.m = make_pipeline(PCA(self.k, random_state=0), LinearDiscriminantAnalysis()).fit(X, y > 0)
        return self

    def score(self, R):
        return self.m.decision_function(pipeline(R, ("absorbance",)))


class _PLSR:
    """PLS regression on absorbance (log10 1/R, mean-centred inside PLS); score = predicted percent.

    SNV is deliberately not applied: it removes the broadband darkening that carries most of
    the seacoal signal (tested: SNV roughly doubles the PLSR error for seacoal)."""
    name = "PLSR"

    def __init__(self, max_components=20):
        self.max_components = max_components

    def fit(self, R, y):
        X = pipeline(R, ("absorbance",))
        self.res = fit_plsr(X, y, self.max_components)
        self.m = self.res["model"]
        return self

    def score(self, R):
        return self.m.predict(pipeline(R, ("absorbance",))).ravel()


class _Classifier:
    def __init__(self, est, name, steps=("absorbance",)):
        self.est, self.name, self.steps = est, name, steps

    def fit(self, R, y):
        self.m = self.est.fit(pipeline(R, self.steps), y > 0)
        return self

    def score(self, R):
        X = pipeline(R, self.steps)
        if hasattr(self.m, "decision_function"):
            return self.m.decision_function(X)
        return self.m.predict_proba(X)[:, 1]


def baselines(seed=0):
    return {
        "PCA-LDA": lambda: _PCA_LDA(10),
        "PLSR": lambda: _PLSR(20),
        "SVM-RBF": lambda: _Classifier(make_pipeline(StandardScaler(), SVC(C=10, gamma="scale")), "SVM-RBF"),
        "RandomForest": lambda: _Classifier(RandomForestClassifier(300, n_jobs=-1, random_state=seed), "RandomForest"),
        "GradientBoosting": lambda: _Classifier(HistGradientBoostingClassifier(random_state=seed), "GradientBoosting"),
    }
