"""Partial least squares regression (PLSR) calibration with cross-validation.

Plain-language summary: PLSR is the standard way to turn an NIR spectrum into a
predicted percentage (for example, percent seacoal). This module fits it,
chooses how many components to keep by cross-validation, and reports the
prediction error.
"""

from __future__ import annotations

import numpy as np
from sklearn.cross_decomposition import PLSRegression
from sklearn.model_selection import KFold, cross_val_predict


def fit_plsr(X, y, max_components=20, cv=5, seed=0, tol=0.01):
    """Fit PLSR, picking the smallest component count within `tol` (relative) of the minimum RMSECV.

    Returns dict with model, n_components, rmsecv, r2cv, cv_pred, rmsecv_curve.
    """
    X = np.asarray(X, float)
    y = np.asarray(y, float).ravel()
    kf = KFold(cv, shuffle=True, random_state=seed)
    max_components = int(min(max_components, X.shape[1], X.shape[0] - X.shape[0] // cv - 1))
    curve, preds = [], []
    for a in range(1, max_components + 1):
        p = cross_val_predict(PLSRegression(a, scale=False), X, y, cv=kf).ravel()
        preds.append(p)
        curve.append(np.sqrt(np.mean((p - y) ** 2)))
    curve = np.array(curve)
    best = int(np.argmax(curve <= curve.min() * (1 + tol))) + 1
    model = PLSRegression(best, scale=False).fit(X, y)
    p = preds[best - 1]
    r2 = 1 - np.sum((p - y) ** 2) / np.sum((y - y.mean()) ** 2)
    return {"model": model, "n_components": best, "rmsecv": float(curve[best - 1]),
            "r2cv": float(r2), "cv_pred": p, "rmsecv_curve": curve}


def classical_lod(pred_blank, y_true, y_pred):
    """IUPAC-style LOD = 3.3 * sd(blank predictions) / calibration slope."""
    slope = np.polyfit(np.asarray(y_true, float), np.asarray(y_pred, float), 1)[0]
    return float(3.3 * np.std(pred_blank, ddof=1) / slope)
