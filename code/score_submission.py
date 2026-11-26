#!/usr/bin/env python3
"""Score a new method on the detection-limit benchmark.

Plain-language summary: if you have your own NIR method, train it on a
benchmark calibration file, give each row of the matching test file a score
(higher = more of the additive), save those scores as a CSV, and run this
script. It applies exactly the same rule as the published baselines and prints
your detection limit. Add --append to put the result on the leaderboard file
(then open a pull request on GitHub to have it listed publicly).

Usage:
  python code/score_submission.py --set GSNIR-bench-v1.0_dry_lab_seacoal --scores my_scores.csv \
      --method "My method" --submitted-by "Name, affiliation" [--append] [--url https://link-to-code]

The scores CSV needs two columns: sample_id, score. Every test sample_id must be present.
Methods may use any training data they like, but must not use the test-set composition columns.
"""

import argparse
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from greensand_nir.benchmark import score_levels  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--set", required=True)
    ap.add_argument("--scores", required=True)
    ap.add_argument("--method", default="unnamed method")
    ap.add_argument("--submitted-by", default="")
    ap.add_argument("--url", default="")
    ap.add_argument("--append", action="store_true")
    a = ap.parse_args()

    test_path = os.path.join(ROOT, "benchmark", "sets", f"{a.set}_test.csv.gz")
    if not os.path.exists(test_path):
        sys.exit(f"no test file for set '{a.set}' (expected {os.path.relpath(test_path, ROOT)})")
    test = pd.read_csv(test_path)
    target = "iron_oxide" if a.set.endswith("iron_oxide") else a.set.rsplit("_", 1)[-1]
    sub = pd.read_csv(a.scores)
    if not {"sample_id", "score"} <= set(sub.columns):
        sys.exit("scores file needs columns sample_id, score")
    dup = sub["sample_id"].duplicated()
    if dup.any():
        sys.exit(f"{int(dup.sum())} sample_id values appear more than once in the scores file")
    sub["score"] = pd.to_numeric(sub["score"], errors="coerce")
    extra = set(sub["sample_id"]) - set(test["sample_id"])
    if extra:
        sys.exit(f"{len(extra)} sample_id values are not in the test set (wrong set?), e.g. {sorted(extra)[:3]}")
    merged = test[["sample_id", f"{target}_pct"]].merge(sub[["sample_id", "score"]], on="sample_id", how="left")
    if not np.isfinite(merged["score"].to_numpy(float)).all():
        sys.exit(f"{int((~np.isfinite(merged['score'].to_numpy(float))).sum())} test samples have a missing or non-numeric score")
    tab, lod, thr, det = score_levels(merged["score"], merged[f"{target}_pct"], details=True)
    print(tab.to_string(index=False))
    print(f"\nDetection limit ({target}): {lod if lod == lod else 'not reached'} %")
    print(f"Lowest level detected: {det['lowest_level_detected']} %; misses higher levels: {det['misses_higher_levels']}")
    if a.append:
        _, track, tier, *_ = a.set.split("_")
        row = {"set": a.set, "track": track, "tier": tier, "target": target, "method": a.method,
               "detection_limit_pct": lod, "submitted_by": a.submitted_by, "url": a.url, **det}
        lbp = os.path.join(ROOT, "benchmark", "leaderboard.csv")
        lb = pd.read_csv(lbp)
        pd.concat([lb, pd.DataFrame([row])], ignore_index=True).to_csv(lbp, index=False)
        print("appended to benchmark/leaderboard.csv; run code/06_figures.py to refresh the leaderboard page")


if __name__ == "__main__":
    main()
