#!/usr/bin/env python3
"""Small censor-aware/exact summary of the Sage experiment output."""
import itertools
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = json.loads((ROOT / "results/sage_analysis.json").read_text())
records = source["semaev_groebner"]["records"]
limit = source["semaev_groebner"]["relation_search_limit"] + 1
by_base = {name: [] for name in ("historical", "random", "nums_full_x")}
for row in records:
    by_base[row["base"]].append(row["relation_k"] if row["relation_k"] is not None else limit)

tests = []
for name in ("historical", "nums_full_x"):
    diffs = [a-b for a,b in zip(by_base[name], by_base["random"])]
    observed = abs(sum(diffs))
    permutations = [abs(sum(sign*d for sign,d in zip(signs,diffs)))
                    for signs in itertools.product((-1,1), repeat=len(diffs))]
    tests.append({"left": name, "right": "random", "pairs": len(diffs),
                  "mean_capped_difference": sum(diffs)/len(diffs),
                  "exact_sign_flip_p_value": sum(value >= observed for value in permutations)/len(permutations)})

division = source["division_polynomials"]["records"]
by_k = {}
for k in range(3, source["division_polynomials"]["max_k"] + 1):
    selected = [row for row in division if row["k"] == k]
    by_k[str(k)] = {"records": len(selected),
                    "min_factor_degree_le_2": sum(row["min_factor_degree"] <= 2 for row in selected),
                    "most_common_factor_patterns": [[list(pattern), count] for pattern,count in
                        Counter(tuple(row["factor_degrees"]) for row in selected).most_common(3)]}

result = {"censor_value": limit, "paired_capped_tests": tests, "division_by_k": by_k,
          "warning": "Capped-rank summaries are exploratory, not a full survival model; n=12."}
(ROOT / "results/sage_summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
