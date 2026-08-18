#!/usr/bin/env sage
"""Solve one blinded, base-conditioned Semaev ideal.

This worker intentionally processes a single job.  The parent process enforces the
timeout, so a stuck Singular C call cannot stall the complete experiment.
"""
import argparse
import json
import resource
import time
from pathlib import Path

from sage.all import GF, PolynomialRing, ZZ, prod


def universal_f3(ring, u, v, t, b):
    return (u-v)**2*t**2 - 2*((u+v)*(u*v)+2*b)*t + (u*v)**2 - 4*b*(u+v)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("job")
    args = parser.parse_args()
    job = json.loads(Path(args.job).read_text())

    field = GF(int(job["p"]))
    arity = int(job["arity"])
    names = tuple(f"u{i}" for i in range(1, arity + 1))
    ring = PolynomialRing(field, names=names, order=job["order"])
    variables = ring.gens()
    b = ring(int(job["b"]))
    q = ring(int(job["target_x"]))

    if arity == 2:
        semaev = universal_f3(ring, variables[0], variables[1], q, b)
    elif arity == 3:
        template_ring = PolynomialRing(ZZ, names=("x1", "x2", "x3", "q", "z", "bb"))
        x1, x2, x3, qt, z, bb = template_ring.gens()
        template = universal_f3(template_ring, x1, x2, z, bb).resultant(
            universal_f3(template_ring, x3, qt, z, bb), z)
        semaev = template_ring.hom(
            [variables[0], variables[1], variables[2], q, ring(0), b], ring)(template)
    else:
        raise ValueError("only arity 2 and 3 are supported")

    factor_base = [field(int(value)) for value in job["factor_base"]]
    equations = [semaev]
    equations.extend(prod(variable - value for value in factor_base) for variable in variables)
    ideal = ring.ideal(equations)

    wall_start = time.monotonic()
    cpu_start = time.process_time()
    basis = ideal.groebner_basis(algorithm="singular:std")
    result = {
        "blind_id": job["blind_id"],
        "status": "completed",
        "wall_seconds": time.monotonic() - wall_start,
        "cpu_seconds": time.process_time() - cpu_start,
        "max_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "basis_size": len(basis),
        "max_basis_degree": max(int(poly.total_degree()) for poly in basis),
        "unit_ideal": list(basis) == [ring(1)],
        "semaev_degree": int(semaev.total_degree()),
        "semaev_terms": len(semaev.dict()),
    }
    print(json.dumps(result, separators=(",", ":")), flush=True)


if __name__ == "__main__":
    main()
