#!/usr/bin/env python3
"""Empirical ranks for the SEC generators in inverse-scalar trait families."""
import argparse
import json
from collections import defaultdict
from pathlib import Path

METRICS = (
    "min_x_bit_length",
    "min_x_hamming_weight",
    "max_leading_zero_bits",
    "max_zero_32_limbs",
    "max_zero_64_limbs",
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = []
    for path in args.input:
        rows.extend(json.loads(line) for line in Path(path).open())
    controls = defaultdict(list)
    special = {}
    for row in rows:
        key = (row["curve"], row["family"])
        if row["point_kind"] == "control":
            controls[key].append(row)
        else:
            special[key] = row
    analyses = []
    for key, group in sorted(controls.items()):
        for metric in METRICS:
            values = sorted(float(row[metric]) for row in group)
            value = float(special[key][metric])
            less = sum(item < value for item in values)
            equal = sum(item == value for item in values)
            n = len(values)
            midrank = (less + 0.5 * equal + 0.5) / (n + 1)
            analyses.append({
                "curve": key[0], "family": key[1], "metric": metric,
                "published_value": value, "witness_k": special[key]["witness_k"][metric],
                "controls": n, "control_min": values[0], "control_median": values[n // 2],
                "control_max": values[-1], "tie_count": equal,
                "lower_tail_midrank": midrank,
                "two_sided_midrank_p": min(1.0, 2 * min(midrank, 1 - midrank)),
            })
    result = {
        "inputs": args.input,
        "records": len(rows),
        "analyses": analyses,
        "interpretation": "The primary family is dissect_1_8. Other families are exploratory and require multiplicity-aware interpretation.",
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"records": len(rows), "endpoints": len(analyses)}, indent=2))


if __name__ == "__main__":
    main()
