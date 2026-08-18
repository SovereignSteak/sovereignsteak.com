#!/usr/bin/env python3
"""Empirical ranks for SEC generator coordinate relations against controls."""
import argparse
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", nargs="+", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    rows=[]
    for name in args.input:
        rows.extend(json.loads(line) for line in Path(name).open())
    groups=defaultdict(list)
    specials={}
    for row in rows:
        key=(row["curve"],row["dimension"])
        if row["point_kind"]=="control": groups[key].append(row)
        else: specials[(row["curve"],row["dimension"],row["point_kind"])]=row
    analyses=[]
    for (curve,dimension),controls in sorted(groups.items()):
        values=sorted(float(row["normalized_log2_l2"]) for row in controls)
        for kind in ("published_g","half_h"):
            row=specials[(curve,dimension,kind)]; value=float(row["normalized_log2_l2"])
            lower=sum(control <= value for control in values)
            analyses.append({"curve":curve,"dimension":dimension,"point_kind":kind,
                "controls":len(values),"normalized_log2_l2":value,
                "lower_tail_rank":lower,"lower_tail_fraction":lower/len(values),
                "two_sided_empirical_p":min(1.0,2*min((lower+1)/(len(values)+1),
                    (len(values)-lower+1)/(len(values)+1)))})
    result={"inputs":args.input,"records":len(rows),"analyses":analyses,
      "primary_endpoint":"normalized log2 Euclidean norm; lower means a shorter relation",
      "trigger":"Replicate any lower-tail fraction below 0.01 using a fresh seed."}
    Path(args.output).write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))


if __name__=="__main__":main()
