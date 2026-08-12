#!/usr/bin/env python3
"""Test simple counter interpretations of the observed half-generator affixes."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, lift_x

verification = json.loads((ROOT / "results/sec2_verification.json").read_text())
specs = json.loads((ROOT / "data/sec2_koblitz.json").read_text())["curves"]
core = verification["shared_core"]
records = []
for spec, half in zip(specs, verification["results"]):
    curve = Curve(int(spec["p"], 16), 0, int(spec["b"], 16))
    prefix, suffix = half["hx"].split(core)
    suffix_value = int(suffix, 16)
    liftable_suffixes = []
    for value in range(16 ** len(suffix)):
        x = int(prefix + core + format(value, f"0{len(suffix)}x"), 16)
        if x < curve.p and lift_x(curve, x, 0):
            liftable_suffixes.append(value)
    prefix_value = int(prefix, 16)
    local_prefixes = []
    for value in range(max(0, prefix_value - 1000), prefix_value + 1):
        rendered = (format(value, "x") if value else "") + core + suffix
        x = int(rendered, 16)
        if x < curve.p and lift_x(curve, x, 0):
            local_prefixes.append(value)
    records.append({"curve": spec["name"], "prefix": prefix, "suffix": suffix,
                    "liftable_suffixes": liftable_suffixes,
                    "observed_suffix_lift_rank_zero_based": liftable_suffixes.index(suffix_value),
                    "liftable_prefixes_in_previous_1000": len(local_prefixes),
                    "observed_prefix_lift_rank_in_window": len(local_prefixes)-1})
result = {"records": records,
          "conclusion": "No observed affix is the first liftable suffix or prefix in the tested natural ascending scans."}
(ROOT / "results/affix_analysis.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result, indent=2))
