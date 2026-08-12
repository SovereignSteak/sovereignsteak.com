#!/usr/bin/env python3
"""Reference high-assurance multi-generator derivation for the SEC 2 curves."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, lift_x


def encode_int(value: int) -> bytes:
    raw = value.to_bytes((value.bit_length() + 7) // 8 or 1, "big")
    return len(raw).to_bytes(2, "big") + raw


def derive(curve: Curve, n: int, transcript: bytes, full_x: bool):
    bits, size = curve.p.bit_length(), (curve.p.bit_length() + 7) // 8
    for counter in range(1 << 32):
        block = hashlib.shake_256(transcript + counter.to_bytes(8, "big")).digest(size + 1)
        x = int.from_bytes(block[:size], "big") & ((1 << bits) - 1)
        if x >= curve.p or (full_x and x.bit_length() != bits):
            continue
        point = lift_x(curve, x, block[-1] & 1)
        if point is not None and curve.mul(n, point) is None:
            return point, counter
    raise RuntimeError("counter exhausted")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, help="public unpredictable seed/beacon, UTF-8")
    parser.add_argument("--protocol", required=True)
    parser.add_argument("--role", default="independent-generator")
    parser.add_argument("--count", type=int, default=2)
    parser.add_argument("--allow-short-x", action="store_true")
    parser.add_argument("--output", default="results/derived_generators.json")
    args = parser.parse_args()
    curves = json.loads((ROOT / "data/sec2_koblitz.json").read_text())["curves"]
    records = []
    for spec in curves:
        vals = {k: int(spec[k], 16) for k in ("p", "a", "b", "n")}
        curve = Curve(vals["p"], vals["a"], vals["b"])
        canonical = b"".join(encode_int(vals[k]) for k in ("p", "a", "b", "n"))
        for index in range(args.count):
            transcript = (b"DLP-GEN-H2P-v1\x00" + encode_int(len(args.protocol.encode())) +
                          args.protocol.encode() + encode_int(len(args.role.encode())) + args.role.encode() +
                          encode_int(len(args.seed.encode())) + args.seed.encode() +
                          encode_int(len(spec["name"].encode())) + spec["name"].encode() +
                          canonical + index.to_bytes(4, "big"))
            point, counter = derive(curve, vals["n"], transcript, not args.allow_short_x)
            records.append({"curve": spec["name"], "index": index, "x": f"{point[0]:x}",
                            "y": f"{point[1]:x}", "counter": counter,
                            "transcript_sha256": hashlib.sha256(transcript).hexdigest()})
    result = {"scheme": "DLP-GEN-H2P-v1", "protocol": args.protocol, "role": args.role,
              "public_seed": args.seed,
              "full_length_x": not args.allow_short_x, "records": records}
    Path(args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
