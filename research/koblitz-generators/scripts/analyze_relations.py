#!/usr/bin/env python3
"""Paired and censor-aware summaries for expanded relation scans."""
import argparse, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np

ap=argparse.ArgumentParser(); ap.add_argument('--input',default='results/relations.jsonl')
ap.add_argument('--output',default='results/relations_analysis.json'); args=ap.parse_args()
rows=[json.loads(x) for x in Path(args.input).open()]
grouped=defaultdict(dict)
for r in rows: grouped[(r['seed'],r['row_index'])][r['base']]=r

def binom_two_sided(b,c):
    n=b+c
    if not n:return 1.0
    tail=sum(math.comb(n,k) for k in range(0,min(b,c)+1))/2**n
    return min(1.0,2*tail)

def compare(left,right):
    pairs=[v for v in grouped.values() if left in v and right in v]
    L=np.array([v[left]['relation_k'] or v[left]['limit']+1 for v in pairs],float)
    R=np.array([v[right]['relation_k'] or v[right]['limit']+1 for v in pairs],float)
    dif=L-R; observed=abs(float(dif.mean())); rng=np.random.default_rng(0x53414745)
    exceed=0; trials=100000
    for start in range(0,trials,500):
        count=min(500,trials-start); signs=rng.integers(0,2,(count,len(dif)),dtype=np.int8)*2-1
        exceed += int(np.count_nonzero(np.abs(signs@dif/len(dif))>=observed))
    ls=np.array([v[left]['relation_k'] is not None for v in pairs]); rs=np.array([v[right]['relation_k'] is not None for v in pairs])
    b=int(np.count_nonzero(ls & ~rs)); c=int(np.count_nonzero(~ls & rs))
    return {'left':left,'right':right,'pairs':len(pairs),'left_successes':int(ls.sum()),
      'right_successes':int(rs.sum()),'discordant_left_only':b,'discordant_right_only':c,
      'mcnemar_exact_p':binom_two_sided(b,c),'mean_capped_difference':float(dif.mean()),
      'paired_sign_flip_p':(exceed+1)/(trials+1),'sign_flip_trials':trials}

by_bits={}
for bits in sorted(set(r['bits'] for r in rows)):
    selected=[r for r in rows if r['bits']==bits]
    by_bits[str(bits)]={name:{'total':sum(r['base']==name for r in selected),
      'successes':sum(r['base']==name and r['relation_k'] is not None for r in selected)}
      for name in ('historical','random','nums_full_x')}
result={'records':len(rows),'matched_curves':len(grouped),'comparisons':[compare('historical','random'),
  compare('nums_full_x','random')],'successes_by_bits':by_bits,
  'censoring_note':'relation_k=None is right-censored at the common per-record limit; capped tests retain it as limit+1.'}
Path(args.output).write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
