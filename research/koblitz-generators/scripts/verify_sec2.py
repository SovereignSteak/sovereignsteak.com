#!/usr/bin/env python3
"""Verify SEC 2 Koblitz generators, their halves, and GLV action."""

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, nontrivial_cube_root

CORE = "8ce563f89a0ed9414f5aa28ad0d96d6795f9c6"


def main() -> None:
    source = json.loads((ROOT / "data/sec2_koblitz.json").read_text())
    results = []
    for item in source["curves"]:
        values = {k: int(item[k], 16) for k in ("p", "a", "b", "gx", "gy", "n")}
        curve = Curve(values["p"], values["a"], values["b"])
        G = values["gx"], values["gy"]
        assert curve.on_curve(G)
        assert curve.mul(values["n"], G) is None
        H = curve.mul(pow(2, -1, values["n"]), G)
        assert H and curve.add(H, H) == G
        hx = format(H[0], "x")
        assert CORE in hx

        beta0 = nontrivial_cube_root(values["p"])
        lambda0 = nontrivial_cube_root(values["n"])
        glv = None
        for beta in (beta0, pow(beta0, 2, values["p"])):
            phi_g = beta * G[0] % values["p"], G[1]
            for lam in (lambda0, pow(lambda0, 2, values["n"])):
                if curve.mul(lam, G) == phi_g:
                    glv = beta, lam, phi_g, (beta * H[0] % values["p"], H[1])
                    assert curve.mul(lam, H) == glv[3]
                    break
            if glv:
                break
        assert glv is not None
        beta, lam, phi_g, phi_h = glv
        results.append({
            "name": item["name"], "hx": f"{H[0]:x}", "hy": f"{H[1]:x}",
            "core_offset_hex_digits": hx.index(CORE),
            "beta": f"{beta:x}", "lambda": f"{lam:x}",
            "phi_gx": f"{phi_g[0]:x}", "phi_gy": f"{phi_g[1]:x}",
            "phi_hx": f"{phi_h[0]:x}", "phi_hy": f"{phi_h[1]:x}"
        })
    out = {"shared_core": CORE, "shared_core_bits": len(CORE) * 4, "results": results}
    target = ROOT / "results/sec2_verification.json"
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
