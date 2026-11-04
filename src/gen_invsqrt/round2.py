"""Signed-digit oracle schedules, derived from Sumit Chongder and Rudra R4/R5.

Changes by this workspace: configurable precisions and split widths; borrow the
normalized leading one for a clean carry; prune the final phase-shift stage
using the promised s<=10 bound. No verifier logic is changed.
"""
from fractions import Fraction
import numpy as np
import kickmix as km
import sumit_reference as H
import signed_digit_lab as A
import deferred_lookup as D
import hybrid_add as B

def prepare(cfg,tabs):
 d=np.arange(1<<H.DB,dtype=np.int64);Rmax=0;spread=0;minimum={};maxima={}
 for key,(k2,k1,k0) in tabs.items():
  r,_=H.pipeline(cfg,k2,k1,d);minimum[key]=int(r.min());maxima[key]=int(r.max());Rmax=max(Rmax,int(r.max()),k1)
  spread=max(spread,int(r.max()-r.min()))
 # Pick the narrowest unsigned residual which also contains the initial K1.
 for block in range(1,Rmax.bit_length()):
  bases={k:v>>block for k,v in minimum.items()}
  if all(0<=tabs[k][1]-(v<<block)<(1<<(block+1)) and maxima[k]-(v<<block)<(1<<(block+1)) for k,v in bases.items()):break
 return {"block":block,"rw":block+1,"cw":Rmax.bit_length()-block,
         "coarse":bases,"residual":{k:tabs[k][1]-(v<<block) for k,v in bases.items()}}

def shift(b,flags,word,L,inverse,prune=True):
 stages=[(1,1),(2,2),(3,4),(4,8)];occ=[];n=L
 for k,d in stages:
  occ.append(min(n,L+2) if prune and k==4 else n);n=min(n+d,len(word))
 seq=list(enumerate(stages));seq=seq[::-1] if inverse else seq
 for j,(k,d) in seq:
  indices=range(occ[j]) if inverse else reversed(range(occ[j]))
  for i in indices:
   if i+d<len(word):
    zero_boundary = i+d >= L+sum(amount for _,amount in stages[:j])
    if zero_boundary:
     if inverse:b.cx(word[i+d],word[i]);b.del_and(flags[k],word[i],word[i+d])
     else:b.init_and(flags[k],word[i],word[i+d]);b.cx(word[i+d],word[i])
    else:b.cswap(flags[k],word[i],word[i+d])

def build(cfg,tabs,*,borrow=True,prune=True,merge=False,parity_input=False,carry_block=None,phase_cut=0,deferred=False,anf=False):
 lay=H.layout(cfg,tabs,LB=cfg.fy-7,S=cfg.fy-8);split=prepare(cfg,tabs)
 b=km.CircuitBuilder();x=b.create_quantum_register(22,name="x");flags=b.alloc_qubits(4 if parity_input else 5)
 f=([x[21]]+list(flags)) if parity_input else flags
 if parity_input:
  for k,amount in H.NSTAGES[:-1]:
   top=x[22-amount:22];b.x(top);H.and_all_into(b,list(top),f[k]);b.x(top)
   for i in reversed(range(22-amount)):b.cswap(f[k],x[i],x[i+amount])
  b.x(x[21]);b.left_rotate(x[:21],1,control=x[21]);b.cx(x[21],x[0])
 else:H.normalize(b,x,f)
 borrowed=[]
 if borrow and not parity_input:b.x(x[21]);borrowed=[x[21]]
 c2,res,coarse,low,high=[b.alloc_qubits(n) for n in [cfg.w2,split["rw"],split["cw"],lay["LB"],lay["whi"]]]
 checkpoints=[]
 def mark(label):
  z=b # stats collected from final tagged operation counts externally when supported
 def add(a,t,cin=None,sub=False):
  if carry_block:return B.add(b,a,t,cin,sub,borrowed=borrowed,prefix=carry_block)
  return A.folded_gadd(b,a,t,cin,sub,borrowed=borrowed)
 full=km.array(list(low)+list(res)+list(c2)+list(high)+list(coarse))
 rest=km.array(list(low)+list(res)+list(c2)+list(coarse));fulltable=[];resttable=[];hightable=[]
 for e in range(2):
  for i in range(128):
   k=(e,i);common=lay["lo"][k]|(split["residual"][k]<<lay["LB"])|(tabs[k][0]<<(lay["LB"]+split["rw"]))
   resttable.append(common|(split["coarse"][k]<<(lay["LB"]+split["rw"]+cfg.w2)))
   fulltable.append(common|(lay["hi"][k]<<(lay["LB"]+split["rw"]+cfg.w2))|(split["coarse"][k]<<(lay["LB"]+split["rw"]+cfg.w2+lay["whi"])))
   hightable.append(lay["hi"][k])
 address=km.array(list(x[14:21])+[f[0]]);delta=x[:14]
 def phase(reg,lowbit):
  ext=b.alloc_qubits(10-len(borrowed));word=km.array(list(reg)+borrowed+list(ext))
  shift(b,f,word,len(reg),False,prune)
  for i,q in enumerate(word):
   exponent=lowbit+i-cfg.fy-10
   if exponent<0 and not(lowbit==cfg.gy and i<phase_cut):b.z_pow(q,Fraction(2)**(exponent+1))
  shift(b,f,word,len(reg),True,prune);b.free(ext)
 def inner(inverse):
  rows=cfg.rrow_list();rows=rows[::-1] if inverse else rows
  for i in rows:
   sh=cfg.sh2[i]
   if sh>=0:a=c2[sh:];t=res;cin=c2[sh-1] if sh else None
   else:a=c2;t=res[-sh:];cin=None
   b.cx(delta[i],t);add(a,t,cin,sub=inverse);b.cx(delta[i],t)
 def outer(derivative,inverse):
  for i in range(14) if inverse else reversed(range(14)):
   sh=cfg.sh1[i]
   if sh>=0:a=derivative[sh:];t=low;cin=derivative[sh-1] if sh else None
   else:a=derivative;t=low[-sh:];cin=None
   b.cx(delta[i],t);add(a,t,cin,sub=inverse);b.cx(delta[i],t)
 b.init_lookup(table=fulltable,address=address,target=full)
 deferred_bits=[]
 if not merge:
  phase(high,lay["S"])
  if deferred:deferred_bits=D.demolish(b,high)
  else:b.del_lookup(table=hightable,address=address,target=high)
  b.free(high)
 inner(False);add(res[split["block"]:],coarse)
 derivative=res[:split["block"]]+coarse
 outer(derivative,False)
 if merge:
  add(low[lay["S"]:],high)
  phase(km.array(list(low[cfg.gy:lay["S"]])+list(high)),cfg.gy)
  add(low[lay["S"]:],high,sub=True)
 else:phase(low[cfg.gy:],cfg.gy)
 outer(derivative,True);add(res[split["block"]:],coarse,sub=True);inner(True)
 remaining=full if merge else rest
 if deferred:
  deferred_bits+=D.demolish(b,remaining);b.free(remaining)
  table=fulltable if merge else [hi|(rr<<lay['whi']) for hi,rr in zip(hightable,resttable)]
  D.repair(b,address,table,deferred_bits,anf=anf)
 else:
  b.del_lookup(table=fulltable if merge else resttable,address=address,target=remaining);b.free(remaining)
 if borrowed:b.x(x[21])
 if parity_input:
  b.cx(x[21],x[0]);b.right_rotate(x[:21],1,control=x[21]);b.x(x[21])
  for k,amount in reversed(H.NSTAGES[:-1]):
   for i in range(22-amount):b.cswap(f[k],x[i],x[i+amount])
   top=x[22-amount:22];m=b.alloc_bits(1)[0];b.hmr(f[k],m);b.push_condition(m)
   b.x(top);H.phase_all(b,list(top));b.x(top);b.pop_condition();b.free(m)
 else:H.unnormalize(b,x,f)
 b.free(flags)
 return b.finish_circuit(),{k:v for k,v in split.items() if k not in ["coarse","residual"]}