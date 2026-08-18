#!/usr/bin/env python3
"""Search bounded GLV coefficient boxes for unusually low-height point coordinates.

For phi(P)=[lambda]P, u*P+v*phi(P)=[u+v*lambda]P.  The scalar set is
curve-level; the resulting coordinates remain base-conditioned.  We deduplicate that
set explicitly so lattice collisions cannot masquerade as extra samples.
"""
import argparse
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, nontrivial_cube_root


def oriented_lambda(curve, n, beta, point):
    image = (beta * point[0] % curve.p, point[1])
    root = nontrivial_cube_root(n)
    for candidate in (root, root * root % n):
        if curve.mul(candidate, point) == image:
            return candidate
    raise ValueError("no lambda orientation matches beta")


def scalar_box(n, lam, bound):
    representatives = {}
    for u in range(-bound, bound + 1):
        for v in range(-bound, bound + 1):
            scalar = (u + v * lam) % n
            if scalar and scalar not in representatives:
                representatives[scalar] = (u, v)
    return representatives


def metric_state():
    return {"centered_x": None, "x_popcount": None, "x_bits": None}, {}


def observe(curve, q, scalar, coefficients, best, witnesses):
    if q is None:
        return
    x = q[0]
    values = {"centered_x": min(x, curve.p-x), "x_popcount": x.bit_count(),
              "x_bits": x.bit_length()}
    for name, value in values.items():
        if best[name] is None or value < best[name]:
            best[name] = value
            witnesses[name] = {"value": value, "u": coefficients[0], "v": coefficients[1],
                               "scalar": str(scalar), "x": str(x)}


def finish_metrics(samples, best, witnesses):
    return {"samples": samples, "min_centered_x": best["centered_x"],
            "log2_min_centered_x": math.log2(max(1, best["centered_x"])),
            "min_x_popcount": best["x_popcount"], "min_x_bits": best["x_bits"],
            "witnesses": witnesses}


def metrics_scalar(curve, point, scalars):
    best, witnesses = metric_state()
    for scalar, coefficients in scalars.items():
        q = curve.mul(scalar, point)
        observe(curve, q, scalar, coefficients, best, witnesses)
    return finish_metrics(len(scalars), best, witnesses)


def metrics_grid(curve, point, n, lam, beta, bound):
    """Walk the coefficient grid with additions instead of one mul per cell."""
    best, witnesses = metric_state()
    phi = (beta * point[0] % curve.p, point[1])
    row_start = curve.add(curve.mul(bound, curve.neg(point)),
                          curve.mul(bound, curve.neg(phi)))
    seen = set()
    for v in range(-bound, bound + 1):
        q = row_start
        for u in range(-bound, bound + 1):
            scalar = (u + v * lam) % n
            if scalar and scalar not in seen:
                seen.add(scalar)
                observe(curve, q, scalar, (u, v), best, witnesses)
            q = curve.add(q, point)
        row_start = curve.add(row_start, phi)
    return finish_metrics(len(seen), best, witnesses)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/high_value_corpus.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--bound", type=int, default=16)
    parser.add_argument("--engine", choices=("grid", "scalar"), default="grid")
    parser.add_argument("--bases", help="comma-separated names; default all")
    args = parser.parse_args()
    rows = [json.loads(line) for line in (ROOT / args.input).open()][args.start:args.start+args.count]
    with (ROOT / args.output).open("w") as output:
        for index, row in enumerate(rows, 1):
            curve = Curve(int(row["p"]), 0, int(row["b"]))
            names = args.bases.split(",") if args.bases else list(row["bases"])
            anchor_data = row["bases"][names[0]]
            anchor = (int(anchor_data["x"]), int(anchor_data["y"]))
            lam = oriented_lambda(curve, int(row["n"]), int(row["beta"]), anchor)
            scalars = scalar_box(int(row["n"]), lam, args.bound) if args.engine == "scalar" else None
            for name in names:
                base = row["bases"][name]
                point = (int(base["x"]), int(base["y"]))
                result = {"seed": row["seed"], "row_index": row["index"], "bits": row["bits"],
                          "base": name, "bound": args.bound, "lambda": str(lam)}
                if args.engine == "scalar":
                    result.update(metrics_scalar(curve, point, scalars))
                else:
                    result.update(metrics_grid(curve, point, int(row["n"]), lam,
                                               int(row["beta"]), args.bound))
                output.write(json.dumps(result, separators=(",", ":")) + "\n")
            if index % 10 == 0:
                print(f"{index}/{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
