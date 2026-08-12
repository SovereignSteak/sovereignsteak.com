#!/usr/bin/env python3
"""Reproducible tests of recipe families; distinguishes evidence from speculation."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERIFY = json.loads((ROOT / "results/sec2_verification.json").read_text())
CORE = VERIFY["shared_core"]


def longest_common_substring(strings: list[str]) -> str:
    shortest = min(strings, key=len)
    for length in range(len(shortest), 0, -1):
        for start in range(len(shortest) - length + 1):
            candidate = shortest[start:start + length]
            if all(candidate in value for value in strings):
                return candidate
    return ""


def main() -> None:
    hxs = [entry["hx"] for entry in VERIFY["results"]]
    lcs = longest_common_substring(hxs)
    assert lcs == CORE
    decompositions = []
    for entry in VERIFY["results"]:
        prefix, suffix = entry["hx"].split(CORE)
        decompositions.append({"name": entry["name"], "prefix": prefix, "core": CORE,
                               "suffix": suffix, "hx_bits": int(entry["hx"], 16).bit_length()})

    # A bounded, declared falsification test, not a claim to exhaust unknown seed formats.
    labels = [b"SECG", b"SEC2", b"Koblitz", b"generator", b"half-generator",
              b"secp160k1", b"secp192k1", b"secp224k1", b"secp256k1"]
    hash_hits = []
    target = bytes.fromhex(CORE)
    for label in labels:
        for counter in range(100_000):
            variants = (label + counter.to_bytes(4, "big"), label + str(counter).encode(),
                        counter.to_bytes(4, "big") + label)
            for message in variants:
                digest = hashlib.sha1(message).digest()
                if target in digest or digest[:19] == target or digest[-19:] == target:
                    hash_hits.append({"message_hex": message.hex(), "sha1": digest.hex()})

    report = {
        "exact_lcs_hex": lcs, "exact_lcs_bits": 4 * len(lcs),
        "decompositions": decompositions,
        "secp224k1_equals_secp256k1_hx": hxs[2] == hxs[3],
        "bounded_sha1_test": {"labels": [x.decode() for x in labels], "counters_per_label": 100000,
                              "encodings": ["label||u32be", "label||decimal", "u32be||label"],
                              "hits": hash_hits},
        "ranking": [
            {"rank": 1, "recipe": "fixed 152-bit hexadecimal core plus curve-specific short prefix/suffix, lift, then double",
             "fit": "exact for all four", "caveat": "descriptive reconstruction; selection rule for affixes is unknown"},
            {"rank": 2, "recipe": "reuse one low-height Hx candidate across sizes, scan nearby affixes until lift/order tests pass, then double",
             "fit": "explains literal equality at 224/256 and low bit length", "caveat": "many scan orders fit retrospectively"},
            {"rank": 3, "recipe": "short seed/counter through SHA-1 or truncated SHA-1, then affix/lift/double",
             "fit": "not reproduced in bounded declared search", "caveat": "unbounded seed space makes this unfalsifiable without provenance"}
        ]
    }
    (ROOT / "results/recipe_analysis.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
