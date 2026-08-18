#!/usr/bin/env python3
"""Fixed-base side-channel proxy screen for the real SEC k1 generators.

This measures public table encodings and high-level mixed-addition Hamming weights. It
does not model a particular CPU, multiplier, compiler, cache, or physical device.
"""
import argparse
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.ec import Curve,lift_x


def control_point(curve,name,seed,index):
    size=(curve.p.bit_length()+7)//8;bits=curve.p.bit_length()
    transcript=b"DLP-GEN-LEAKAGE-v1\0"+seed.encode()+b"\0"+name.encode()+index.to_bytes(8,"big")
    for counter in range(1<<32):
        block=hashlib.shake_256(transcript+counter.to_bytes(8,"big")).digest(size+1)
        x=int.from_bytes(block[:size],"big")&((1<<bits)-1)
        if x>=curve.p:continue
        point=lift_x(curve,x,block[-1]&1)
        if point:return point,counter,hashlib.sha256(transcript).hexdigest()
    raise RuntimeError("control derivation exhausted")


def j_double(q,p):
    X,Y,Z=q
    if Y==0 or Z==0:return (0,1,0)
    A=X*X%p;B=Y*Y%p;C=B*B%p;D=2*((X+B)*(X+B)-A-C)%p
    E=3*A%p;F=E*E%p;X3=(F-2*D)%p
    return X3,(E*(D-X3)-8*C)%p,2*Y*Z%p


def j_add_mixed_trace(q,point,p):
    X1,Y1,Z1=q;x2,y2=point
    if Z1==0:return (x2,y2,1),[x2,y2,1]
    Z2=Z1*Z1%p;U2=x2*Z2%p;S2=y2*Z1*Z2%p;H=(U2-X1)%p
    if H==0:
        result=j_double(q,p) if S2==Y1 else (0,1,0)
        return result,[Z2,U2,S2,H,*result]
    HH=H*H%p;I=4*HH%p;J=H*I%p;r=2*(S2-Y1)%p;V=X1*I%p
    X3=(r*r-J-2*V)%p;Y3=(r*(V-X3)-2*Y1*J)%p;Z3=2*Z1*H%p
    return (X3,Y3,Z3),[Z2,U2,S2,H,HH,I,J,r,V,X3,Y3,Z3]


def affine_table(curve,point,count):
    # One inversion per point is acceptable at this campaign size and keeps this
    # independent of the projective scanner under test.
    table=[];q=None
    for _ in range(count):
        q=curve.add(q,point);table.append(q)
    return table


def encoded_value(point,p,representation):
    x,y=point
    if representation=="montgomery":
        limbs=(p.bit_length()+63)//64;R=pow(2,64*limbs,p);x=x*R%p;y=y*R%p
    return x|(y<<p.bit_length()),x,y


def table_metrics(points,p,representation,word_bits):
    encoded=[];zero_counts=[];entry_weights=[]
    width=(p.bit_length()+word_bits-1)//word_bits;mask=(1<<word_bits)-1
    for point in points:
        packed,x,y=encoded_value(point,p,representation);encoded.append(packed)
        entry_weights.append(packed.bit_count())
        limbs=[(value>>(word_bits*i))&mask for value in (x,y) for i in range(width)]
        zero_counts.append(sum(value==0 for value in limbs))
    distances=[(encoded[i]^encoded[j]).bit_count() for i in range(len(encoded)) for j in range(i)]
    return {"entry1_hw":entry_weights[0],"min_entry_hw":min(entry_weights),
      "mean_entry_hw":statistics.fmean(entry_weights),"max_zero_limbs":max(zero_counts),
      "entry1_zero_limbs":zero_counts[0],"min_pairwise_hd":min(distances),
      "mean_pairwise_hd":statistics.fmean(distances)}


def mixed_trace_metrics(curve,point,table):
    vectors=[]
    # Fixed public prefix scalars create representative nontrivial Jacobian states.
    for scalar in (17,29,43,61):
        affine=curve.mul(scalar,point);state=(affine[0],affine[1],1)
        for selected in table[:15]:
            _,trace=j_add_mixed_trace(state,selected,curve.p)
            vectors.append([value.bit_count() for value in trace])
    distances=[]
    for block in range(4):
        group=vectors[block*15:(block+1)*15]
        distances.extend(sum(abs(a-b) for a,b in zip(group[i],group[j]))
                         for i in range(15) for j in range(i))
    entry1=[]
    for block in range(4):
        group=vectors[block*15:(block+1)*15];target=sum(group[0])
        others=[sum(v) for v in group[1:]]
        entry1.append(abs(target-statistics.fmean(others)))
    return {"trace_min_pair_l1":min(distances),"trace_mean_pair_l1":statistics.fmean(distances),
            "trace_entry1_mean_deviation":statistics.fmean(entry1)}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--curve",required=True);ap.add_argument("--count",type=int,default=1000)
    ap.add_argument("--start",type=int,default=0);ap.add_argument("--seed",default="fixed-base-leakage-discovery-v1")
    ap.add_argument("--output",required=True);args=ap.parse_args()
    spec=next(x for x in json.loads((ROOT/"data/sec2_koblitz.json").read_text())["curves"] if x["name"]==args.curve)
    vals={k:int(spec[k],16) for k in ("p","a","b","gx","gy","n")};curve=Curve(vals["p"],0,vals["b"])
    G=(vals["gx"],vals["gy"]);H=curve.mul(pow(2,-1,vals["n"]),G)
    points=[("published_g",None,G,None,None),("half_h",None,H,None,None)]
    for index in range(args.start,args.start+args.count):
        P,counter,digest=control_point(curve,args.curve,args.seed,index);points.append(("control",index,P,counter,digest))
    with (ROOT/args.output).open("w") as out:
        for position,(kind,index,point,counter,digest) in enumerate(points,1):
            table=affine_table(curve,point,255)
            common={"schema":"fixed-base-leakage-v1","curve":args.curve,"point_kind":kind,
                    "control_index":index,"seed":args.seed,"counter":counter,"transcript_sha256":digest}
            for window in (4,5,8):
                subset=table[:(1<<window)-1]
                for representation in ("standard","montgomery"):
                    for word_bits in (32,64):
                        record={**common,"model":"table","window":window,"representation":representation,"word_bits":word_bits}
                        record.update(table_metrics(subset,curve.p,representation,word_bits));out.write(json.dumps(record,separators=(",", ":"))+"\n")
            record={**common,"model":"mixed_trace","window":4,"representation":"standard","word_bits":None}
            record.update(mixed_trace_metrics(curve,point,table));out.write(json.dumps(record,separators=(",", ":"))+"\n")
            out.flush()
            if position%50==0:print(f"{args.curve}: {position}/{len(points)}",flush=True)


if __name__=="__main__":main()
