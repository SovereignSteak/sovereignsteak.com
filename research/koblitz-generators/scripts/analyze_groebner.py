#!/usr/bin/env python3
"""Censor-aware summaries for process-isolated Gröbner runs."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in Path(args.input).open()]
    groups = defaultdict(list)
    for row in rows:
        target_kind = "witnessed" if row["relation_k"] is not None else "censored_probe"
        groups[(row["base"], row["order"], target_kind)].append(row)
    summaries = []
    for (base, order, target_kind), records in sorted(groups.items()):
        completed = [r for r in records if r["status"] == "completed"]
        times = sorted(r["process_wall_seconds"] for r in completed)
        summaries.append({
            "base": base, "order": order, "target_kind": target_kind, "jobs": len(records),
            "completed": len(completed), "timeouts": sum(r["status"] == "timeout" for r in records),
            "errors": sum(r["status"] == "error" for r in records),
            "completion_rate": len(completed)/len(records),
            "median_completed_wall_seconds": times[len(times)//2] if times else None,
            "max_completed_basis_degree": max((r["max_basis_degree"] for r in completed), default=None),
        })
    result = {
        "input": args.input, "jobs": len(rows), "summaries": summaries,
        "warning": "Completed-only timing medians are descriptive, not a comparison under censoring. Compare timeout incidence within matched curves and use survival analysis for a full campaign."
    }
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
