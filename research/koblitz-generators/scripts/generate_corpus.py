#!/usr/bin/env python3
"""Generate deterministic j=0 prime-order curves and three base-selection styles."""

import argparse
import hashlib
import json
import random
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, is_probable_prime, lift_x, nontrivial_cube_root

CORE = int("8ce563f89a0ed9414f5aa28ad0d96d6795f9c6", 16)


def xof_candidate(tag: bytes, index: int, modulus: int) -> int | None:
    """An exactly uniform candidate in [0,modulus), or None on rejection."""
    bits = modulus.bit_length()
    size = (bits + 7) // 8
    raw = hashlib.shake_256(tag + index.to_bytes(8, "big")).digest(size)
    value = int.from_bytes(raw, "big") & ((1 << bits) - 1)
    return value if value < modulus else None


def hash_base(curve: Curve, tag: bytes, full_length: bool) -> tuple[tuple[int, int], int]:
    threshold = 1 << (curve.p.bit_length() - 1)
    for counter in range(1_000_000):
        x = xof_candidate(tag, counter, curve.p)
        if x is None:
            continue
        if full_length and x < threshold:
            continue
        parity = hashlib.shake_256(tag + b"/sign" + counter.to_bytes(8, "big")).digest(1)[0] & 1
        point = lift_x(curve, x, parity)
        if point is not None:
            return point, counter
    raise RuntimeError("hash-to-point rejection bound exceeded")


def historical_base(curve: Curve) -> tuple[tuple[int, int], int, tuple[int, int]]:
    start = CORE % curve.p
    for delta in range(1_000_000):
        h = lift_x(curve, (start + delta) % curve.p, 0)
        if h is not None:
            return curve.add(h, h), delta, h
    raise RuntimeError("historical scan failed")


def find_curve(rng: random.Random, bits: int):
    # p=u^2+3v^2 guarantees p=1 mod 3; j=0 then has the efficient cube-root map.
    half = bits // 2
    while True:
        u = rng.randrange(1 << (half - 1), 1 << half)
        v = rng.randrange(1 << (half - 2), 1 << half)
        p = u * u + 3 * v * v
        if p.bit_length() != bits or not is_probable_prime(p):
            continue
        traces = sorted({2*u, -2*u, u+3*v, -(u+3*v), u-3*v, -(u-3*v)})
        candidates = [(t, p + 1 - t) for t in traces if is_probable_prime(p + 1 - t)]
        if not candidates:
            continue
        for b in range(1, 32):
            curve = Curve(p, 0, b)
            sample = next((lift_x(curve, x, 0) for x in range(1, 100) if lift_x(curve, x, 0)), None)
            if sample is None:
                continue
            for trace, n in candidates:
                if curve.mul(n, sample) is None:
                    # A second point excludes an accidental annihilation (n is prime).
                    sample2 = next((lift_x(curve, x, 1) for x in range(101, 300) if lift_x(curve, x, 1)), None)
                    if sample2 is not None and curve.mul(n, sample2) is None:
                        return curve, n, trace, u, v


def orbit_metrics(curve: Curve, point, beta: int, limit: int = 32) -> dict:
    min_abs_x, min_popcount, zeros = curve.p, curve.p.bit_length(), 0
    for k in range(1, limit + 1):
        q = curve.mul(k, point)
        for i in range(3):
            x = q[0]
            centered = min(x, curve.p - x)
            min_abs_x = min(min_abs_x, centered)
            min_popcount = min(min_popcount, x.bit_count())
            zeros += int(x == 0)
            q = (beta * q[0] % curve.p, q[1])
    return {"orbit_limit": limit, "min_centered_x": str(min_abs_x),
            "min_x_popcount": min_popcount, "zero_x_count": zeros}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=3000)
    parser.add_argument("--seed", default="dlp-gen-corpus-v1")
    parser.add_argument("--output", default="data/corpus.jsonl")
    args = parser.parse_args()
    rng = random.Random(int.from_bytes(hashlib.sha256(args.seed.encode()).digest(), "big"))
    output = ROOT / args.output
    output.parent.mkdir(exist_ok=True)
    with output.open("w") as stream:
        for index in range(args.count):
            bits = 30 + index % 51
            curve, n, trace, u, v = find_curve(rng, bits)
            beta = nontrivial_cube_root(curve.p)
            hist, delta, half_point = historical_base(curve)
            random_base, random_counter = hash_base(curve, f"{args.seed}/random/{index}".encode(), False)
            nums_base, nums_counter = hash_base(curve, f"{args.seed}/NUMS/v1/{index}".encode(), True)
            assert all(curve.mul(n, q) is None for q in (hist, random_base, nums_base))
            bases = {}
            for name, point, counter in (("historical", hist, delta), ("random", random_base, random_counter),
                                         ("nums_full_x", nums_base, nums_counter)):
                bases[name] = {"x": str(point[0]), "y": str(point[1]), "counter": counter,
                               "x_bits": point[0].bit_length(), **orbit_metrics(curve, point, beta)}
            row = {"schema": 1, "index": index, "seed": args.seed, "bits": bits,
                   "p": str(curve.p), "a": 0, "b": curve.b, "n": str(n), "h": 1,
                   "trace": trace, "cm_u": u, "cm_v": v, "beta": str(beta),
                   "historical_hx": str(half_point[0]), "bases": bases,
                   "curve_invariants": {"j": 0, "discriminant_nonzero": True,
                     "psi3_terms_a0": 2, "psi3_degree": 4,
                     "note": "division polynomials are curve/base-independent"}}
            stream.write(json.dumps(row, separators=(",", ":")) + "\n")
            if (index + 1) % 100 == 0:
                print(f"generated {index + 1}/{args.count}", flush=True)


if __name__ == "__main__":
    main()
