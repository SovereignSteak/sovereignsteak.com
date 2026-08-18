#!/usr/bin/env sage
"""LLL search for short modular relations among x([k]P) on SEC k1 curves."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from sage.all import EllipticCurve, GF, Matrix, ZZ

ROOT = Path(__file__).resolve().parents[1]


def encoded(value):
    raw = int(value).to_bytes((int(value).bit_length()+7)//8 or 1, "big")
    return len(raw).to_bytes(2, "big") + raw


def control_point(field, curve, spec, seed, index):
    p = int(spec["p"], 16)
    bits, size = p.bit_length(), (p.bit_length()+7)//8
    transcript = (b"DLP-GEN-LLL-CONTROL-v1\x00" + encoded(len(seed)) + seed.encode() +
                  encoded(len(spec["name"])) + spec["name"].encode() +
                  index.to_bytes(8, "big"))
    for counter in range(1 << 32):
        block = hashlib.shake_256(transcript + counter.to_bytes(8, "big")).digest(size+1)
        x = int.from_bytes(block[:size], "big") & ((1 << bits)-1)
        if x >= p or not curve.is_x_coord(field(x)):
            continue
        points = curve.lift_x(field(x), all=True)
        point = points[block[-1] & 1] if len(points) == 2 else points[0]
        return point, counter, hashlib.sha256(transcript).hexdigest()
    raise RuntimeError("control counter exhausted")


def relation(curve, point, p, dimension):
    coordinates = []
    q = point
    for _ in range(dimension):
        coordinates.append(int(q[0]))
        q += point
    # The large last-coordinate weight forces LLL to prefer an exact modular
    # relation over a merely small nonzero residue.
    weight = p
    rows = []
    for i, x in enumerate(coordinates):
        row = [0] * (dimension+1)
        row[i] = 1
        row[-1] = weight*x
        rows.append(row)
    rows.append([0]*dimension + [weight*p])
    reduced = Matrix(ZZ, rows).LLL()
    candidates = []
    for row in reduced.rows():
        if row[-1] != 0 or not any(row[:-1]):
            continue
        coefficients = [int(value) for value in row[:-1]]
        residual = sum(c*x for c, x in zip(coefficients, coordinates)) % p
        assert residual == 0
        l2_squared = sum(c*c for c in coefficients)
        candidates.append((l2_squared, max(abs(c) for c in coefficients), coefficients))
    if not candidates:
        raise RuntimeError("LLL returned no exact relation; increase weight")
    l2_squared, linf, coefficients = min(candidates)
    return {
        "coordinates": [str(x) for x in coordinates],
        "coefficients": [str(c) for c in coefficients],
        "l2_squared": str(l2_squared),
        "log2_l2": math.log2(l2_squared)/2,
        "normalized_log2_l2": math.log2(l2_squared)/2 - math.log2(p)/dimension,
        "linf": str(linf),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--curve", required=True)
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--dimensions", default="6,8,10,12")
    parser.add_argument("--seed", default="sec-k1-lll-discovery-v1")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    specs = json.loads((ROOT/"data/sec2_koblitz.json").read_text())["curves"]
    spec = next(item for item in specs if item["name"] == args.curve)
    p, b, n = (int(spec[name], 16) for name in ("p", "b", "n"))
    field = GF(p)
    curve = EllipticCurve(field, [0, b])
    generator = curve(int(spec["gx"],16), int(spec["gy"],16))
    half = pow(2, -1, n)*generator
    dimensions = [int(value) for value in args.dimensions.split(",")]
    with (ROOT/args.output).open("w") as output:
        points = [("published_g", None, generator, None, None),
                  ("half_h", None, half, None, None)]
        for index in range(args.start, args.start+args.count):
            point, counter, digest = control_point(field, curve, spec, args.seed, index)
            points.append(("control", index, point, counter, digest))
        for position, (kind, index, point, counter, digest) in enumerate(points, 1):
            for dimension in dimensions:
                record = {"schema":"sec-k1-lll-v1", "curve":args.curve, "p":str(p),
                          "point_kind":kind, "control_index":index, "seed":args.seed,
                          "counter":counter, "transcript_sha256":digest,
                          "dimension":dimension, "point_x":str(int(point[0])),
                          "point_y":str(int(point[1]))}
                record.update(relation(curve, point, p, dimension))
                output.write(json.dumps(record,separators=(",", ":"))+"\n")
            output.flush()
            if position % 100 == 0:
                print(f"{args.curve}: {position}/{len(points)}", flush=True)


if __name__ == "__main__":
    main()
