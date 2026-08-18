#!/usr/bin/env python3
"""Measure DiSSECT-style inverse-scalar coordinate traits on the SEC k1 curves.

For a base P and nonzero scalar k this evaluates x([k^-1 mod n]P).  The primary
family is exactly k=1,...,8.  Additional families are explicitly exploratory.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, lift_x


def control_point(curve, name, seed, index):
    size = (curve.p.bit_length() + 7) // 8
    bits = curve.p.bit_length()
    transcript = b"DLP-GEN-INVERSE-TRAIT-v1\0" + seed.encode() + b"\0" + name.encode() + index.to_bytes(8, "big")
    for counter in range(1 << 32):
        block = hashlib.shake_256(transcript + counter.to_bytes(8, "big")).digest(size + 1)
        x = int.from_bytes(block[:size], "big") & ((1 << bits) - 1)
        if x >= curve.p:
            continue
        point = lift_x(curve, x, block[-1] & 1)
        if point is not None:
            return point, counter, hashlib.sha256(transcript).hexdigest()
    raise RuntimeError("control derivation exhausted")


def scalar_families(order, lam):
    families = {
        "dissect_1_8": list(range(1, 9)),
        "small_1_32": list(range(1, 33)),
        "powers_of_two": [1 << i for i in range(9)],
        "low_weight_8bit": [k for k in range(1, 256) if k.bit_count() <= 2],
    }
    glv = set()
    for u in range(-4, 5):
        for v in range(-4, 5):
            scalar = (u + v * lam) % order
            if scalar:
                # x(Q) does not distinguish scalar signs.
                glv.add(min(scalar, order - scalar))
    families["glv_box_4"] = sorted(glv)
    return families


def zero_limbs(value, field_bits, word_bits):
    width = (field_bits + word_bits - 1) // word_bits
    mask = (1 << word_bits) - 1
    return sum(((value >> (word_bits * i)) & mask) == 0 for i in range(width))


def jacobian_double(q, p):
    x, y, z = q
    if y == 0 or z == 0:
        return 0, 1, 0
    yy = y * y % p
    s = 4 * x * yy % p
    m = 3 * x * x % p
    x3 = (m * m - 2 * s) % p
    return x3, (m * (s - x3) - 8 * yy * yy) % p, 2 * y * z % p


def jacobian_add(left, right, p):
    x1, y1, z1 = left
    x2, y2, z2 = right
    if z1 == 0:
        return right
    if z2 == 0:
        return left
    z1z1 = z1 * z1 % p
    z2z2 = z2 * z2 % p
    u1 = x1 * z2z2 % p
    u2 = x2 * z1z1 % p
    s1 = y1 * z2 * z2z2 % p
    s2 = y2 * z1 * z1z1 % p
    if u1 == u2:
        return jacobian_double(left, p) if s1 == s2 else (0, 1, 0)
    h = (u2 - u1) % p
    r = (s2 - s1) % p
    hh = h * h % p
    hhh = h * hh % p
    u1hh = u1 * hh % p
    x3 = (r * r - hhh - 2 * u1hh) % p
    return x3, (r * (u1hh - x3) - s1 * hhh) % p, h * z1 * z2 % p


def scalar_mul_jacobian(curve, scalar, point):
    result = (0, 1, 0)
    addend = (point[0], point[1], 1)
    while scalar:
        if scalar & 1:
            result = jacobian_add(result, addend, curve.p)
        addend = jacobian_double(addend, curve.p)
        scalar >>= 1
    return result


def scalar_mul_x(curve, scalar, point):
    result = scalar_mul_jacobian(curve, scalar, point)
    if result[2] == 0:
        raise AssertionError("nonzero scalar produced infinity")
    z_inv = pow(result[2], -1, curve.p)
    return result[0] * z_inv * z_inv % curve.p


def inverse_x_batch(curve, order, point, scalars):
    scalars = sorted(set(scalars))
    projective = [scalar_mul_jacobian(curve, pow(k, -1, order), point) for k in scalars]
    if any(q[2] == 0 for q in projective):
        raise AssertionError("nonzero inverse scalar produced infinity")
    prefixes = []
    product = 1
    for q in projective:
        prefixes.append(product)
        product = product * q[2] % curve.p
    inverse = pow(product, -1, curve.p)
    z_inverses = [0] * len(projective)
    for index in range(len(projective) - 1, -1, -1):
        z_inverses[index] = inverse * prefixes[index] % curve.p
        inverse = inverse * projective[index][2] % curve.p
    return {k: q[0] * z_inv * z_inv % curve.p for k, q, z_inv in zip(scalars, projective, z_inverses)}


def family_metrics(curve, scalars, x_values, include_values=False):
    observations = []
    for scalar in scalars:
        x = x_values[scalar]
        observations.append({
            "k": hex(scalar),
            "x": hex(x) if include_values else None,
            "x_bit_length": x.bit_length(),
            "x_hamming_weight": x.bit_count(),
            "leading_zero_bits": curve.p.bit_length() - x.bit_length(),
            "zero_32_limbs": zero_limbs(x, curve.p.bit_length(), 32),
            "zero_64_limbs": zero_limbs(x, curve.p.bit_length(), 64),
        })
    metrics = {
        "min_x_bit_length": min(o["x_bit_length"] for o in observations),
        "min_x_hamming_weight": min(o["x_hamming_weight"] for o in observations),
        "max_leading_zero_bits": max(o["leading_zero_bits"] for o in observations),
        "max_zero_32_limbs": max(o["zero_32_limbs"] for o in observations),
        "max_zero_64_limbs": max(o["zero_64_limbs"] for o in observations),
    }
    metrics["witness_k"] = {
        metric: next(o["k"] for o in observations if o[field] == value)
        for metric, field, value in (
            ("min_x_bit_length", "x_bit_length", metrics["min_x_bit_length"]),
            ("min_x_hamming_weight", "x_hamming_weight", metrics["min_x_hamming_weight"]),
            ("max_leading_zero_bits", "leading_zero_bits", metrics["max_leading_zero_bits"]),
            ("max_zero_32_limbs", "zero_32_limbs", metrics["max_zero_32_limbs"]),
            ("max_zero_64_limbs", "zero_64_limbs", metrics["max_zero_64_limbs"]),
        )
    }
    if include_values:
        metrics["observations"] = observations
    return metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--seed", default="inverse-scalar-traits-v1")
    parser.add_argument("--families", default="all", help="all or comma-separated family names")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    specs = json.loads((ROOT / "data/sec2_koblitz.json").read_text())["curves"]
    verified = {r["name"]: r for r in json.loads((ROOT / "results/sec2_verification.json").read_text())["results"]}
    with (ROOT / args.output).open("w") as out:
        for spec in specs:
            values = {key: int(spec[key], 16) for key in ("p", "a", "b", "gx", "gy", "n")}
            curve = Curve(values["p"], values["a"], values["b"])
            families = scalar_families(values["n"], int(verified[spec["name"]]["lambda"], 16))
            selected = families if args.families == "all" else {name: families[name] for name in args.families.split(",")}
            points = [("published_g", None, (values["gx"], values["gy"]), None, None)]
            for index in range(args.start, args.start + args.count):
                point, counter, digest = control_point(curve, spec["name"], args.seed, index)
                points.append(("control", index, point, counter, digest))
            for position, (kind, index, point, counter, digest) in enumerate(points, 1):
                x_values = inverse_x_batch(curve, values["n"], point,
                                           [k for scalars in selected.values() for k in scalars])
                for name, scalars in selected.items():
                    record = {
                        "schema": "inverse-scalar-traits-v1",
                        "curve": spec["name"],
                        "point_kind": kind,
                        "control_index": index,
                        "seed": args.seed,
                        "counter": counter,
                        "transcript_sha256": digest,
                        "family": name,
                        "scalar_count": len(scalars),
                    }
                    record.update(family_metrics(curve, scalars, x_values, kind == "published_g"))
                    out.write(json.dumps(record, separators=(",", ":")) + "\n")
                out.flush()
                if position % 250 == 0:
                    print(f"{spec['name']}: {position}/{len(points)}", flush=True)


if __name__ == "__main__":
    main()
