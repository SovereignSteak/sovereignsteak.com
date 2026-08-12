#!/usr/bin/env python3
"""Generate preregistered curves with multiple independent exact-uniform controls."""
import argparse,hashlib,json,random,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.generate_corpus import find_curve,historical_base,hash_base
from src.ec import nontrivial_cube_root

ap=argparse.ArgumentParser();ap.add_argument('--start',type=int,required=True);ap.add_argument('--count',type=int,required=True)
ap.add_argument('--seed',default='high-value-f4-v1');ap.add_argument('--output',required=True);args=ap.parse_args()
with (ROOT/args.output).open('w') as out:
 for offset in range(args.count):
  index=args.start+offset;bits=30+index%7
  rng=random.Random(int.from_bytes(hashlib.sha256(f'{args.seed}/curve/{index}'.encode()).digest(),'big'))
  curve,n,trace,u,v=find_curve(rng,bits);beta=nontrivial_cube_root(curve.p)
  historical,delta,H=historical_base(curve)
  nums,nc=hash_base(curve,f'{args.seed}/NUMS/{index}'.encode(),True)
  bases={'historical':{'x':str(historical[0]),'y':str(historical[1]),'counter':delta},
         'nums_full_x':{'x':str(nums[0]),'y':str(nums[1]),'counter':nc}}
  for control in range(8):
   P,counter=hash_base(curve,f'{args.seed}/uniform-control/{control}/{index}'.encode(),False)
   bases[f'random_{control}']={'x':str(P[0]),'y':str(P[1]),'counter':counter}
  assert all(curve.mul(n,(int(P['x']),int(P['y']))) is None for P in bases.values())
  row={'schema':'high-value-f4-v1','index':index,'seed':args.seed,'bits':bits,'p':str(curve.p),
       'a':0,'b':curve.b,'n':str(n),'h':1,'trace':trace,'cm_u':u,'cm_v':v,'beta':str(beta),
       'historical_hx':str(H[0]),'bases':bases}
  out.write(json.dumps(row,separators=(',',':'))+'\n')
  if (offset+1)%10==0:print(f'{offset+1}/{args.count}',flush=True)
