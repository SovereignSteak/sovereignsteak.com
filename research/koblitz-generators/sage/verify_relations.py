#!/usr/bin/env sage
"""Independently verify expanded relation witnesses and selected Singular bases."""
import argparse,json
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing,prod

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--input',default='results/relations.jsonl')
ap.add_argument('--groebner-limit',type=int,default=60); ap.add_argument('--output',default='results/relations_sage_verification.json')
args=ap.parse_args(); rows=[json.loads(x) for x in (ROOT/args.input).open()]
corpus={}
for line in (ROOT/'data/corpus.jsonl').open():
 r=json.loads(line); corpus[(r['seed'],r['index'])]=r
checked=0; failures=[]; groebner=[]
for witness in rows:
 if witness['relation_k'] is None: continue
 row=corpus[(witness['seed'],witness['row_index'])]; F=GF(int(row['p'])); E=EllipticCurve(F,[0,row['b']])
 base=row['bases'][witness['base']]; P=E(int(base['x']),int(base['y'])); Q=witness['relation_k']*P
 if int(Q[0])!=witness['target_x']:
  failures.append({'row':witness['row_index'],'base':witness['base'],'kind':'scalar_witness'}); continue
 fb=[]; x=0
 while len(fb)<witness['factor_base_size']:
  if E.is_x_coord(x):fb.append(x)
  x+=1
 R=PolynomialRing(F,names=('x1','x2'),order='lex'); x1,x2=R.gens(); xq=Q[0]; b=row['b']
 f3=(x1-x2)**2*xq**2-2*((x1+x2)*(x1*x2)+2*b)*xq+(x1*x2)**2-4*b*(x1+x2)
 solutions=sum(1 for u in fb for v in fb if f3(x1=u,x2=v)==0)
 if not solutions: failures.append({'row':witness['row_index'],'base':witness['base'],'kind':'semaev'})
 elif len(groebner)<args.groebner_limit:
  basis=R.ideal([prod(x1-u for u in fb),prod(x2-u for u in fb),f3]).groebner_basis(algorithm='singular:std')
  groebner.append({'row':witness['row_index'],'base':witness['base'],'solutions':solutions,
    'basis_size':len(basis),'max_degree':max(int(g.total_degree()) for g in basis),'unit_ideal':list(basis)==[R(1)]})
 checked+=1
result={'witnesses_checked':checked,'failures':failures,'groebner_checked':len(groebner),'groebner':groebner}
(ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='groebner'},indent=2))
