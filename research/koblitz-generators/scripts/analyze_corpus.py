#!/usr/bin/env python3
"""Paired analysis with deterministic sign-flip randomization tests."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import numpy as np


def paired_summary(rows, left, right, metric, transforms=lambda x: x):
    differences = np.array([transforms(int(r["bases"][left][metric])) -
                            transforms(int(r["bases"][right][metric])) for r in rows], dtype=float)
    observed = abs(float(differences.mean()))
    rng = np.random.default_rng(0x53454347)
    exceed = 0
    trials = 10000
    for start in range(0, trials, 500):
        count = min(500, trials - start)
        signs = rng.integers(0, 2, size=(count, len(differences)), dtype=np.int8) * 2 - 1
        values = np.abs(signs @ differences / len(differences))
        exceed += int(np.count_nonzero(values >= observed))
    return {"left": left, "right": right, "metric": metric, "pairs": len(differences),
            "mean_paired_difference": float(differences.mean()),
            "median_paired_difference": float(np.median(differences)),
            "sign_flip_p_value": (exceed + 1) / (trials + 1), "trials": trials}


def slope(rows, base, metric):
    x = np.array([r["bits"] for r in rows], dtype=float)
    y = np.array([math.log2(max(1, int(r["bases"][base][metric]))) for r in rows])
    return float(np.polyfit(x, y, 1)[0])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/corpus.jsonl")
    parser.add_argument("--output", default="results/corpus_analysis.json")
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).open()]
    comparisons = []
    for left in ("historical", "nums_full_x"):
        comparisons.extend([
            paired_summary(rows, left, "random", "x_bits"),
            paired_summary(rows, left, "random", "min_x_popcount"),
            paired_summary(rows, left, "random", "min_centered_x", lambda x: math.log2(max(1, x)))])
    core_hx = [r["historical_hx"] for r in rows]
    result = {"input": args.input, "sha256": hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
              "curves": len(rows), "bit_range": [min(r["bits"] for r in rows), max(r["bits"] for r in rows)],
              "comparisons": comparisons,
              "scaling_log2_min_centered_x_per_field_bit": {
                  base: slope(rows, base, "min_centered_x") for base in ("historical", "random", "nums_full_x")},
              "cross_curve": {"unique_historical_hx": len(set(core_hx)),
                 "duplicate_count": len(core_hx) - len(set(core_hx)),
                 "interpretation": "modular reduction of one public core intentionally couples historical-style scans"},
              "structural_findings": {
                "division_polynomials": "Identical across all bases on a fixed curve; base comparison is inapplicable. psi_3 has two nonzero terms for every a=0 curve.",
                "glv_lattice": "Depends only on (n, lambda), not the chosen nonzero base in a prime-order group; no base-specific correlation exists at this level.",
                "summation_systems": "Base affects the target constants, so timings can fluctuate, but no CAS was available; no Groebner timing claim is made.",
                "orbit_scan": "Exact k<=32 and all three GLV images; paired statistics reported above."
              }}
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
