#!/usr/bin/env sage
"""SageMath extension: independent validation, division factors, toy Semaev systems."""

import argparse
import hashlib
import json
from pathlib import Path

from sage.all import EllipticCurve, GF, PolynomialRing, prod, cputime, version

ROOT = Path(__file__).resolve().parents[1]


def sec2_validation():
    specs = json.loads((ROOT / "data/sec2_koblitz.json").read_text())["curves"]
    halves = {x["name"]: x for x in json.loads(
        (ROOT / "results/sec2_verification.json").read_text())["results"]}
    output = []
    for spec in specs:
        v = {k: int(spec[k], 16) for k in ("p", "a", "b", "gx", "gy", "n")}
        E = EllipticCurve(GF(v["p"]), [v["a"], v["b"]])
        G = E(v["gx"], v["gy"])
        H = E(int(halves[spec["name"]]["hx"], 16), int(halves[spec["name"]]["hy"], 16))
        output.append({"name": spec["name"], "sage_order": str(E.order()),
                       "declared_order": str(v["n"]), "order_matches": E.order() == v["n"],
                       "generator_order_matches": G.order() == v["n"], "double_half_matches": 2*H == G})
    return output


def load_rows(limit=None):
    rows = []
    with (ROOT / "data/corpus.jsonl").open() as source:
        for line in source:
            rows.append(json.loads(line))
            if limit and len(rows) >= limit:
                break
    return rows


def validate_corpus(rows):
    failures = []
    for row in rows:
        p, n = int(row["p"]), int(row["n"])
        E = EllipticCurve(GF(p), [0, row["b"]])
        if E.order() != n:
            failures.append({"index": row["index"], "kind": "order"})
            continue
        for kind, base in row["bases"].items():
            P = E(int(base["x"]), int(base["y"]))
            if P.order() != n:
                failures.append({"index": row["index"], "kind": kind})
    return {"checked": len(rows), "failures": failures}


def division_experiment(rows, max_k):
    records = []
    for row in rows:
        p = int(row["p"])
        E = EllipticCurve(GF(p), [0, row["b"]])
        for k in range(3, max_k + 1):
            psi = E.division_polynomial(k)
            factors = psi.factor()
            degrees = sorted([int(f.degree()) for f, exponent in factors for _ in range(exponent)])
            records.append({"row": row["index"], "bits": row["bits"], "b": row["b"],
                            "k": k, "degree": int(psi.degree()), "term_count": len(psi.dict()),
                            "factor_degrees": degrees, "min_factor_degree": min(degrees)})
    low = sum(r["min_factor_degree"] <= 2 for r in records)
    return {"curves": len(rows), "max_k": max_k, "records": records,
            "low_degree_factor_records": low,
            "interpretation": "Each record is identical for historical/random/NUMS bases on its curve."}


def liftable_xs(E, count):
    values, x = [], 0
    while len(values) < count:
        if E.is_x_coord(x):
            values.append(x)
        x += 1
    return values


def semaev_experiment(rows, factor_base_size, relation_search_limit):
    records = []
    for row in rows:
        p, b = int(row["p"]), row["b"]
        field = GF(p)
        E = EllipticCurve(field, [0, b])
        factor_base = liftable_xs(E, factor_base_size)
        signed_points = []
        for value in factor_base:
            signed_points.extend(E.lift_x(field(value), all=True))
        pair_target_x = set()
        for left in signed_points:
            for right in signed_points:
                total = left + right
                if not total.is_zero():
                    pair_target_x.add(int(total[0]))
        R = PolynomialRing(field, names=("x1", "x2"), order="lex")
        x1, x2 = R.gens()
        FB1 = prod(x1 - value for value in factor_base)
        FB2 = prod(x2 - value for value in factor_base)
        for base_kind in ("historical", "random", "nums_full_x"):
            P = E(int(row["bases"][base_kind]["x"]), int(row["bases"][base_kind]["y"]))
            Q = P
            relation_k = None
            for k in range(1, relation_search_limit + 1):
                if int(Q[0]) in pair_target_x:
                    relation_k = k
                    break
                Q += P
            if relation_k is None:
                records.append({"row": row["index"], "bits": row["bits"], "base": base_kind,
                                "relation_k": None, "censored_at": relation_search_limit})
                continue
            xq = Q[0]
            # Semaev f_3(x1,x2,xq) for y^2=x^3+b.
            f3 = ((x1-x2)**2 * xq**2 - 2*((x1+x2)*(x1*x2) + 2*b)*xq
                  + (x1*x2)**2 - 4*b*(x1+x2))
            start = cputime()
            basis = R.ideal([FB1, FB2, f3]).groebner_basis(algorithm="singular:std")
            elapsed = cputime(start)
            solutions = sum(1 for left in factor_base for right in factor_base
                            if f3(x1=left, x2=right) == 0)
            records.append({"row": row["index"], "bits": row["bits"], "base": base_kind,
                            "relation_k": relation_k, "censored_at": relation_search_limit,
                            "cpu_seconds": float(elapsed), "basis_size": len(basis),
                            "max_basis_degree": max(int(g.total_degree()) for g in basis),
                            "ordered_x_pair_solutions": solutions})
    return {"curves": len(rows), "factor_base_size": factor_base_size,
            "relation_search_limit": relation_search_limit, "records": records,
            "system": "<f3(x1,x2,xQ), product(x1-B), product(x2-B)> in GF(p)[x1,x2], lex"}


def summarize_semaev(records):
    kinds = ("historical", "random", "nums_full_x")
    grouped = {kind: [r for r in records if r["base"] == kind] for kind in kinds}
    def median(values):
        values = sorted(values)
        m = len(values)//2
        return values[m] if len(values)%2 else (values[m-1]+values[m])/2
    result = {}
    for kind, vals in grouped.items():
        solved = [r for r in vals if r.get("relation_k") is not None]
        result[kind] = {"relations_found": len(solved), "relations_censored": len(vals)-len(solved),
                        "median_relation_k_found": median([r["relation_k"] for r in solved]) if solved else None,
                        "median_cpu_seconds": median([r["cpu_seconds"] for r in solved]) if solved else None,
                        "mean_cpu_seconds": sum(r["cpu_seconds"] for r in solved)/len(solved) if solved else None,
                        "mean_max_basis_degree": sum(r["max_basis_degree"] for r in solved)/len(solved) if solved else None}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-count", type=int, default=2000)
    parser.add_argument("--division-count", type=int, default=120)
    parser.add_argument("--division-max-k", type=int, default=12)
    parser.add_argument("--semaev-count", type=int, default=120)
    parser.add_argument("--factor-base-size", type=int, default=48)
    parser.add_argument("--relation-search-limit", type=int, default=500000)
    parser.add_argument("--output", default="results/sage_analysis.json")
    args = parser.parse_args()
    rows = load_rows(args.validate_count)
    small_rows = [r for r in rows if r["bits"] <= 40][:args.semaev_count]
    division_rows = rows[:args.division_count]
    semaev = semaev_experiment(small_rows, args.factor_base_size, args.relation_search_limit)
    result = {"sage_version": version(), "corpus_sha256": hashlib.sha256(
                  (ROOT / "data/corpus.jsonl").read_bytes()).hexdigest(),
              "sec2": sec2_validation(), "corpus_validation": validate_corpus(rows),
              "division_polynomials": division_experiment(division_rows, args.division_max_k),
              "semaev_groebner": semaev,
              "semaev_summary": summarize_semaev(semaev["records"])}
    (ROOT / args.output).write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"sage_version": result["sage_version"], "sec2": result["sec2"],
                      "corpus_validation": result["corpus_validation"],
                      "division_summary": {k:v for k,v in result["division_polynomials"].items() if k != "records"},
                      "semaev_summary": result["semaev_summary"]}, indent=2))

if __name__ == "__main__":
    main()
