#!/usr/bin/env python3
"""Joint exchangeability test across the preregistered factor-base grid."""
import json
from collections import defaultdict
from pathlib import Path
import numpy as np

SIZES=(12,16,24,32);CONTROLS=[f'random_{i}' for i in range(8)];TRIALS=100000
settings=[]
for size in SIZES:
 grouped=defaultdict(dict)
 for line in Path(f'results/high_value_b{size}.jsonl').open():
  r=json.loads(line);grouped[(r['seed'],r['row_index'])][r['base']]=r
 settings.append(grouped)
keys=sorted(settings[0]);rng=np.random.default_rng(0x47524944)

def matrix(target,outcome):
 names=[target]+CONTROLS; data=np.empty((len(keys),len(names),len(SIZES)),float)
 for si,setting in enumerate(settings):
  for ci,key in enumerate(keys):
   for bi,name in enumerate(names):
    row=setting[key][name]
    data[ci,bi,si]=int(row['relation_k'] is not None) if outcome=='success' else (row['relation_k'] or row['limit']+1)
 return data

def analyze(target,outcome):
 data=matrix(target,outcome);collapsed=data.mean(axis=2);diff=collapsed[:,0]-collapsed[:,1:].mean(axis=1)
 observed=float(diff.mean());exceed=0
 for start in range(0,TRIALS,500):
  count=min(500,TRIALS-start);choice=rng.integers(0,9,(count,len(keys)))
  selected=np.take_along_axis(np.broadcast_to(collapsed,(count,)+collapsed.shape),choice[:,:,None],axis=2)[:,:,0]
  stats=np.mean(selected-(collapsed.sum(axis=1)[None,:]-selected)/8,axis=1)
  exceed+=int(np.count_nonzero(np.abs(stats)>=abs(observed)))
 estimates=[]
 for start in range(0,TRIALS,1000):
  count=min(1000,TRIALS-start);idx=rng.integers(0,len(diff),(count,len(diff)));estimates.append(diff[idx].mean(axis=1))
 estimates=np.concatenate(estimates)
 ranks=[]
 for curve in range(len(keys)):
  per_setting=[]
  for si in range(len(SIZES)):
   row=data[curve,:,si];per_setting.append(1+np.count_nonzero(row<row[0])+.5*(np.count_nonzero(row==row[0])-1))
  ranks.append(np.mean(per_setting))
 return {'outcome':outcome,'target_mean':float(collapsed[:,0].mean()),'control_mean':float(collapsed[:,1:].mean()),
  'mean_difference':observed,'cluster_bootstrap_95_ci':[float(np.quantile(estimates,.025)),float(np.quantile(estimates,.975))],
  'joint_exchangeability_p':(exceed+1)/(TRIALS+1),'mean_rank_across_settings':float(np.mean(ranks))}

result={'factor_base_sizes':SIZES,'curves':len(keys),'controls_per_curve':8,'permutation_rule':'one pseudo-target label per curve, held fixed across all settings',
 'analyses':[{ 'target':target,'outcomes':[analyze(target,'success'),analyze(target,'capped_relation_index')]}
             for target in ('historical','nums_full_x')]}
Path('results/high_value_grid_analysis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
