#!/usr/bin/env python3
"""Empirical special-point ranks for fixed-base leakage proxies."""
import argparse,json
from collections import defaultdict
from pathlib import Path

METRICS={"table":("entry1_hw","min_entry_hw","max_zero_limbs","entry1_zero_limbs","min_pairwise_hd","mean_pairwise_hd"),
         "mixed_trace":("trace_min_pair_l1","trace_mean_pair_l1","trace_entry1_mean_deviation")}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--input",nargs="+",required=True);ap.add_argument("--output",required=True);args=ap.parse_args()
 rows=[]
 for name in args.input:rows.extend(json.loads(x) for x in Path(name).open())
 groups=defaultdict(list);special={}
 for r in rows:
  key=(r["curve"],r["model"],r["window"],r["representation"],r["word_bits"])
  if r["point_kind"]=="control":groups[key].append(r)
  else:special[key+(r["point_kind"],)]=r
 analyses=[]
 for key,controls in sorted(groups.items(),key=str):
  for metric in METRICS[key[1]]:
   values=sorted(float(r[metric]) for r in controls)
   for kind in ("published_g","half_h"):
    value=float(special[key+(kind,)][metric]);less=sum(x<value for x in values);equal=sum(x==value for x in values);n=len(values)
    midrank=(less+0.5*equal+0.5)/(n+1)
    analyses.append({"curve":key[0],"model":key[1],"window":key[2],"representation":key[3],"word_bits":key[4],
      "metric":metric,"point_kind":kind,"value":value,"controls":n,"lower_tail_midrank":midrank,
      "tie_count":equal,"two_sided_midrank_p":min(1.0,2*min(midrank,1-midrank))})
 result={"inputs":args.input,"records":len(rows),"analyses":analyses,
  "warning":"These are public-data Hamming-weight proxies, not measured timing or power traces. Correlated endpoints require multiplicity control and fresh replication."}
 Path(args.output).write_text(json.dumps(result,indent=2)+"\n");print(json.dumps({"records":len(rows),"endpoints":len(analyses)},indent=2))

if __name__=="__main__":main()
