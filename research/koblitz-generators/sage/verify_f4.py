#!/usr/bin/env sage
"""Verify three-summand witnesses using resultant-defined Semaev f_4 and Singular."""
import argparse,json,time,signal
from pathlib import Path
from sage.all import EllipticCurve,GF,PolynomialRing,prod,ZZ

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument('--input',default='results/relations_f4.jsonl')
ap.add_argument('--groebner-limit',type=int,default=30); ap.add_argument('--output',default='results/relations_f4_sage.json')
ap.add_argument('--timeout-seconds',type=int,default=15)
args=ap.parse_args(); witnesses=[json.loads(x) for x in (ROOT/args.input).open()]
# Compute the universal j=0 Semaev f_4 template once over ZZ, then specialize.
S=PolynomialRing(ZZ,names=('x1','x2','x3','q','z','bb')); x1,x2,x3,q,z,bb=S.gens()
def universal_f3(u,v,t):return (u-v)**2*t**2-2*((u+v)*(u*v)+2*bb)*t+(u*v)**2-4*bb*(u+v)
F4_TEMPLATE=universal_f3(x1,x2,z).resultant(universal_f3(x3,q,z),z)
corpus={}
for line in (ROOT/'data/corpus.jsonl').open():
 r=json.loads(line); corpus[(r['seed'],r['index'])]=r
failures=[]; records=[]; checked=0
for w in witnesses:
 if w['relation_k'] is None: continue
 row=corpus[(w['seed'],w['row_index'])]; F=GF(int(row['p'])); E=EllipticCurve(F,[0,row['b']]); b=F(row['b'])
 base=row['bases'][w['base']]; P=E(int(base['x']),int(base['y'])); Q=w['relation_k']*P
 if int(Q[0])!=w['target_x']:
  failures.append({'row':w['row_index'],'base':w['base'],'kind':'scalar'});continue
 fb=[]; signed=[]; value=0
 while len(fb)<w['factor_base_size']:
  if E.is_x_coord(value):
   fb.append(value); signed.extend(E.lift_x(F(value),all=True))
  value+=1
 pair_sums={}
 for A in signed:
  for B in signed:
   total=A+B
   if not total.is_zero():pair_sums[(int(total[0]),int(total[1]))]=(int(A[0]),int(B[0]))
 triple=None
 for C in signed:
  for target in (Q,-Q):
   needed=target-C
   if not needed.is_zero() and (int(needed[0]),int(needed[1])) in pair_sums:
    pair=pair_sums[(int(needed[0]),int(needed[1]))];triple=(pair[0],pair[1],int(C[0]));break
  if triple:break
 if triple is None:
  failures.append({'row':w['row_index'],'base':w['base'],'kind':'triple'});continue
 checked+=1
 if len(records)>=args.groebner_limit:continue
 T=PolynomialRing(F,names=('u1','u2','u3'),order='lex');u1,u2,u3=T.gens()
 f4=S.hom([u1,u2,u3,T(int(Q[0])),T(0),T(row['b'])],T)(F4_TEMPLATE)
 if f4(*triple)!=0:
  failures.append({'row':w['row_index'],'base':w['base'],'kind':'f4'});continue
 ideal=T.ideal([f4,prod(u1-a for a in fb),prod(u2-a for a in fb),prod(u3-a for a in fb)])
 def timed_out(signum,frame):raise TimeoutError('Groebner timeout')
 old_handler=signal.signal(signal.SIGALRM,timed_out); signal.alarm(args.timeout_seconds); start=time.process_time()
 try:basis=ideal.groebner_basis(algorithm='singular:std')
 except TimeoutError:
  records.append({'row':w['row_index'],'base':w['base'],'f4_total_degree':int(f4.total_degree()),
   'f4_terms':len(f4.dict()),'timeout':True,'timeout_seconds':args.timeout_seconds});signal.alarm(0);signal.signal(signal.SIGALRM,old_handler);continue
 signal.alarm(0);signal.signal(signal.SIGALRM,old_handler);elapsed=time.process_time()-start
 records.append({'row':w['row_index'],'base':w['base'],'f4_total_degree':int(f4.total_degree()),
  'f4_terms':len(f4.dict()),'timeout':False,'cpu_seconds':elapsed,'basis_size':len(basis),
  'max_basis_degree':max(int(g.total_degree()) for g in basis),'unit_ideal':list(basis)==[T(1)]})
result={'witnesses_checked':checked,'failures':failures,'groebner_checked':len(records),'records':records}
(ROOT/args.output).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
