#!/usr/bin/env python3
"""Within-curve exchangeability analysis for GLV coefficient-box scans."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

import numpy as np


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, nargs="+")
    parser.add_argument("--output", required=True)
    parser.add_argument("--trials", type=int, default=100000)
    args = parser.parse_args()
    rows = []
    for input_name in args.input:
        rows.extend(json.loads(line) for line in Path(input_name).open())
    grouped = defaultdict(dict)
    for row in rows:
        grouped[(row["seed"], row["row_index"])][row["base"]] = row
    curves = list(grouped.values())
    controls = sorted((name for name in curves[0] if name.startswith("random_")),
                      key=lambda name: int(name.split("_")[1]))
    rng = np.random.default_rng(0x474c5642)
    analyses = []
    for target in ("historical", "nums_full_x"):
        if target not in curves[0]:
            continue
        for metric in ("log2_min_centered_x", "min_x_popcount", "min_x_bits"):
            names = [target] + controls
            matrix = np.asarray([[curve[name][metric] for name in names] for curve in curves], float)
            observed = float(np.mean(matrix[:, 0] - matrix[:, 1:].mean(axis=1)))
            exceed = 0
            for start in range(0, args.trials, 500):
                count = min(500, args.trials-start)
                choices = rng.integers(0, len(names), size=(count, len(curves)))
                expanded = np.broadcast_to(matrix, (count,) + matrix.shape)
                selected = np.take_along_axis(expanded, choices[:, :, None], axis=2)[:, :, 0]
                stats = np.mean(selected - (matrix.sum(axis=1)[None, :] - selected) / len(controls), axis=1)
                exceed += int(np.count_nonzero(np.abs(stats) >= abs(observed)))
            analyses.append({"target": target, "metric": metric, "curves": len(curves),
                             "controls": len(controls), "mean_target_minus_controls": observed,
                             "exchangeability_p": (exceed+1)/(args.trials+1)})
    result = {"input": args.input, "analyses": analyses,
              "interpretation": "The GLV coefficient set is identical for all bases on each curve; only its image coordinates differ."}
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
