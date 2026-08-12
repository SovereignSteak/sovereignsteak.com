#!/usr/bin/env python3
"""Adaptive replication: derive uniform controls 8..15 on the fixed 1,000 curves."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.generate_corpus import hash_base
from src.ec import Curve

with (ROOT/'data/high_value_controls_8_15.jsonl').open('w') as out:
 for row_number,line in enumerate((ROOT/'data/high_value_corpus.jsonl').open(),1):
  source=json.loads(line);curve=Curve(int(source['p']),0,source['b']);bases={}
  for control in range(8,16):
   P,counter=hash_base(curve,f"{source['seed']}/uniform-control/{control}/{source['index']}".encode(),False)
   assert curve.mul(int(source['n']),P) is None
   bases[f'random_{control}']={'x':str(P[0]),'y':str(P[1]),'counter':counter}
  row={k:source[k] for k in ('schema','index','seed','bits','p','a','b','n','h','trace','cm_u','cm_v','beta','historical_hx')}
  row['schema']='high-value-f4-v1-adaptive-controls-8-15';row['bases']=bases
  out.write(json.dumps(row,separators=(',',':'))+'\n')
  if row_number%100==0:print(f'{row_number}/1000',flush=True)
