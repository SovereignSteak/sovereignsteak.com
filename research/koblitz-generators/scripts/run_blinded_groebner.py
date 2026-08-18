#!/usr/bin/env python3
"""Run one Semaev/Singular job per subprocess with blinding and hard timeouts."""
import argparse
import concurrent.futures
import hashlib
import json
import os
import random
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve


def load_corpus(path):
    result = {}
    for line in path.open():
        row = json.loads(line)
        result[(row["seed"], row["index"])] = row
    return result


def factor_base_x(p, b, size):
    # Euler's criterion is sufficient because every corpus prime is odd.
    values = []
    candidate = 0
    while len(values) < size:
        rhs = (candidate**3 + b) % p
        if rhs == 0 or pow(rhs, (p-1)//2, p) == 1:
            values.append(candidate)
        candidate += 1
    return values


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--relations", required=True)
    parser.add_argument("--corpus", default="data/high_value_corpus.jsonl")
    parser.add_argument("--output", required=True)
    parser.add_argument("--timeout-seconds", type=float, default=30)
    parser.add_argument("--orders", default="degrevlex,deglex,lex")
    parser.add_argument("--max-jobs", type=int)
    parser.add_argument("--max-curves", type=int,
                        help="Keep complete matched base sets for this many curve keys")
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", default="blinded-groebner-v1")
    parser.add_argument("--include-censored", action="store_true",
                        help="For misses, test the exact target Q=[limit+1]P")
    args = parser.parse_args()

    corpus = load_corpus(ROOT / args.corpus)
    relations = [json.loads(line) for line in (ROOT / args.relations).open()]
    selected = [r for r in relations if r["relation_k"] is not None or args.include_censored]
    if args.max_curves is not None:
        keys = []
        for relation in selected:
            key = (relation["seed"], relation["row_index"])
            if key not in keys:
                keys.append(key)
        keep = set(keys[:args.max_curves])
        selected = [r for r in selected if (r["seed"], r["row_index"]) in keep]
    orders = [value.strip() for value in args.orders.split(",") if value.strip()]
    jobs = []
    for relation in selected:
        row = corpus[(relation["seed"], relation["row_index"])]
        target_x = relation["target_x"]
        if relation["relation_k"] is None:
            curve = Curve(int(row["p"]), 0, int(row["b"]))
            base = row["bases"][relation["base"]]
            target = curve.mul(int(relation["limit"]) + 1, (int(base["x"]), int(base["y"])))
            if target is None:
                continue
            target_x = target[0]
        for order in orders:
            identity = f'{relation["seed"]}/{relation["row_index"]}/{relation["base"]}/{relation["arity"]}/{relation["factor_base_size"]}/{order}'
            blind_id = hashlib.sha256(f"{args.seed}/{identity}".encode()).hexdigest()[:20]
            jobs.append({
                "blind_id": blind_id,
                "p": row["p"], "b": row["b"], "arity": relation["arity"],
                "target_x": target_x,
                "factor_base": factor_base_x(int(row["p"]), int(row["b"]), relation["factor_base_size"]),
                "order": order,
                "private": {
                    "seed": relation["seed"], "row_index": relation["row_index"],
                    "base": relation["base"], "relation_k": relation["relation_k"],
                    "factor_base_size": relation["factor_base_size"], "arity": relation["arity"],
                },
            })
    random.Random(args.seed).shuffle(jobs)
    if args.max_jobs is not None:
        jobs = jobs[:args.max_jobs]

    worker = ROOT / "sage/groebner_worker.py"
    output_path = ROOT / args.output
    with output_path.open("w") as output, tempfile.TemporaryDirectory(prefix="koblitz-gb-") as temp:
        temp_path = Path(temp)
        environment = os.environ.copy()
        environment["DOT_SAGE"] = str(temp_path / "sage")

        def execute(job):
            public_job = {key: value for key, value in job.items() if key != "private"}
            job_path = temp_path / f'{job["blind_id"]}.json'
            job_path.write_text(json.dumps(public_job))
            started = time.monotonic()
            try:
                run = subprocess.run(
                    ["sage", str(worker), str(job_path)], text=True, capture_output=True,
                    timeout=args.timeout_seconds, cwd=ROOT, env=environment)
                elapsed = time.monotonic() - started
                if run.returncode == 0:
                    record = json.loads(run.stdout.strip().splitlines()[-1])
                else:
                    record = {"blind_id": job["blind_id"], "status": "error",
                              "returncode": run.returncode, "stderr": run.stderr[-2000:]}
                record["process_wall_seconds"] = elapsed
            except subprocess.TimeoutExpired:
                record = {"blind_id": job["blind_id"], "status": "timeout",
                          "process_wall_seconds": time.monotonic() - started,
                          "timeout_seconds": args.timeout_seconds}
            # Unblind only after the worker has exited.
            record.update(job["private"])
            record["order"] = job["order"]
            return record

        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = [pool.submit(execute, job) for job in jobs]
            for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
                record = future.result()
                output.write(json.dumps(record, separators=(",", ":")) + "\n")
                output.flush()
                print(f"{index}/{len(jobs)} {record['status']}", flush=True)


if __name__ == "__main__":
    main()
