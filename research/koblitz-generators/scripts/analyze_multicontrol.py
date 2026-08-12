#!/usr/bin/env python3
"""Within-curve exchangeability analysis with multiple uniform controls."""
import argparse,json
from collections import defaultdict
from pathlib import Path
import numpy as np

ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--output',required=True)
ap.add_argument('--trials',type=int,default=100000);args=ap.parse_args()
rows=[json.loads(x) for x in Path(args.input).open()]; grouped=defaultdict(dict)
for r in rows:grouped[(r['seed'],r['row_index'])][r['base']]=r
curves=list(grouped.values());controls=sorted((name for name in curves[0] if name.startswith('random_')),
 key=lambda name:int(name.split('_')[1]));rng=np.random.default_rng(0x485631)

def values(outcome,target):
 names=[target]+controls; matrix=[]
 for curve in curves:
  if outcome=='success':matrix.append([int(curve[n]['relation_k'] is not None) for n in names])
  else:matrix.append([curve[n]['relation_k'] or curve[n]['limit']+1 for n in names])
 return np.asarray(matrix,dtype=float)

def permutation_test(matrix):
 observed=float(np.mean(matrix[:,0]-matrix[:,1:].mean(axis=1)));exceed=0
 for start in range(0,args.trials,500):
  count=min(500,args.trials-start); choice=rng.integers(0,len(controls)+1,size=(count,len(matrix)))
  selected=np.take_along_axis(np.broadcast_to(matrix,(count,)+matrix.shape),choice[:,:,None],axis=2)[:,:,0]
  stats=np.mean(selected-(matrix.sum(axis=1)[None,:]-selected)/len(controls),axis=1)
  exceed += int(np.count_nonzero(np.abs(stats)>=abs(observed)))
 return observed,(exceed+1)/(args.trials+1)

def bootstrap_ci(differences):
 estimates=[]
 for start in range(0,args.trials,1000):
  count=min(1000,args.trials-start);idx=rng.integers(0,len(differences),(count,len(differences)))
  estimates.append(differences[idx].mean(axis=1))
 estimates=np.concatenate(estimates);return [float(np.quantile(estimates,.025)),float(np.quantile(estimates,.975))]

def analyze(target):
 result={'target':target,'curves':len(curves)}
 for outcome in ('success','capped_relation_index'):
  matrix=values(outcome,target);effect,p=permutation_test(matrix);diff=matrix[:,0]-matrix[:,1:].mean(axis=1)
  ranks=[]
  for row in matrix:
   ranks.append(1+np.count_nonzero(row<row[0])+.5*(np.count_nonzero(row==row[0])-1))
  result[outcome]={'target_mean':float(matrix[:,0].mean()),'control_mean':float(matrix[:,1:].mean()),
    'mean_difference':effect,'cluster_bootstrap_95_ci':bootstrap_ci(diff),'exchangeability_p':p,
    'mean_target_rank':float(np.mean(ranks)),'expected_null_rank':(len(controls)+2)/2}
 return result

result={'input':args.input,'records':len(rows),'matched_curves':len(curves),'controls_per_curve':len(controls),
 'trials':args.trials,'analyses':[analyze('historical'),analyze('nums_full_x')],
 'interpretation':'Lower capped index/rank means an earlier relation; success is 1 when observed before censoring.'}
Path(args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
