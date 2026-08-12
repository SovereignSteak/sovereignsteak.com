#!/usr/bin/env python3
"""Fast batched-projective scan for two-factor-base relations in generator orbits."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.ec import Curve, lift_x


def j_double(Q, p):
    X, Y, Z = Q
    if Y == 0 or Z == 0:
        return (0, 1, 0)
    A = X*X % p; B = Y*Y % p; C = B*B % p
    D = 2*((X+B)*(X+B)-A-C) % p
    E = 3*A % p; F = E*E % p
    return ((F-2*D) % p, (E*(D-(F-2*D))-8*C) % p, (2*Y*Z) % p)


def j_add_mixed(Q, P, p):
    X1, Y1, Z1 = Q; x2, y2 = P
    if Z1 == 0:
        return (x2, y2, 1)
    Z2 = Z1*Z1 % p; U2 = x2*Z2 % p; S2 = y2*Z1*Z2 % p
    H = (U2-X1) % p
    if H == 0:
        return j_double(Q, p) if S2 == Y1 else (0, 1, 0)
    HH = H*H % p; I = 4*HH % p; J = H*I % p
    r = 2*(S2-Y1) % p; V = X1*I % p
    X3 = (r*r-J-2*V) % p
    return X3, (r*(V-X3)-2*Y1*J) % p, (2*Z1*H) % p


def affine_x_batch(points, p):
    prefix, product = [], 1
    for _,_,z in points:
        prefix.append(product)
        product = product*z % p
    inverse = pow(product, p-2, p)
    output = [0]*len(points)
    for i in range(len(points)-1, -1, -1):
        X,_,z = points[i]
        zi = inverse*prefix[i] % p
        inverse = inverse*z % p
        output[i] = X*zi*zi % p
    return output


def first_relation(curve, point, targets, limit, block_size):
    Q = (point[0], point[1], 1)
    k = 1
    while k <= limit:
        block = []
        for _ in range(min(block_size, limit-k+1)):
            block.append(Q)
            Q = j_add_mixed(Q, point, curve.p)
        for offset, x in enumerate(affine_x_batch(block, curve.p)):
            if x in targets:
                return k + offset, x
        k += len(block)
    return None, None


def factor_targets(curve, size, arity):
    xs=[]; value=0
    while len(xs)<size:
        if lift_x(curve,value,0): xs.append(value)
        value += 1
    points=[]
    for x in xs:
        P=lift_x(curve,x,0); points.extend((P,curve.neg(P)))
    sums = points
    for _ in range(arity - 1):
        next_sums=[]
        for P in sums:
            for Q in points:
                S=curve.add(P,Q)
                if S is not None: next_sums.append(S)
        # Point deduplication prevents exponential duplication from permutations/signs.
        sums=list(set(next_sums))
    targets={P[0] for P in sums}
    return xs,targets


def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--start',type=int,default=0)
    ap.add_argument('--count',type=int,default=100); ap.add_argument('--factor-base-size',type=int,default=48)
    ap.add_argument('--limit',type=int,default=500000); ap.add_argument('--block-size',type=int,default=2048)
    ap.add_argument('--arity',type=int,choices=(2,3),default=2)
    ap.add_argument('--input',default='data/corpus.jsonl')
    ap.add_argument('--bases',help='comma-separated base names; default is every base in each row')
    ap.add_argument('--output',required=True); args=ap.parse_args()
    rows=[]
    for line in (ROOT/args.input).open():
        row=json.loads(line)
        if row['bits']<=40:rows.append(row)
    rows=rows[args.start:args.start+args.count]
    with (ROOT/args.output).open('w') as out:
        for pos,row in enumerate(rows):
            curve=Curve(int(row['p']),0,row['b']); fb,targets=factor_targets(curve,args.factor_base_size,args.arity)
            base_names=args.bases.split(',') if args.bases else list(row['bases'])
            for kind in base_names:
                base=row['bases'][kind]; point=(int(base['x']),int(base['y']))
                k,x=first_relation(curve,point,targets,args.limit,args.block_size)
                out.write(json.dumps({'row_index':row['index'],'seed':row['seed'],'bits':row['bits'],
                    'p':row['p'],'b':row['b'],'base':kind,'factor_base_size':args.factor_base_size,
                    'arity':args.arity,
                    'target_x_count':len(targets),'limit':args.limit,'relation_k':k,'target_x':x})+'\n')
            if (pos+1)%10==0: print(f'{pos+1}/{len(rows)}',flush=True)

if __name__=='__main__': main()
