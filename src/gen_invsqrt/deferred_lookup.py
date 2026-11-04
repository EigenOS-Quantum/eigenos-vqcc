"""Deferred lookup demolition and shared one-hot/unary phase repair.

The scheduling idea follows Gu, Kemeny, Yelin and Lukin's Gaussian circuit
(andigu/uncompute, commit 64b5a13aa249f1360846657392e6c66817b26d0f).
This is a new implementation against the kickmix API, Apache-2.0.
"""
import kickmix as km

def demolish(b, register):
 bits=b.alloc_bits(len(register))
 for q,m in zip(register,bits):b.hmr(q,m)
 return list(bits)

def repair_anf(b,address,table,measurements,low_bits=4):
 """Möbius-transform the truth table and share monomials of each half."""
 address=list(address);bits=list(measurements);coef=list(table)
 for i in range(len(address)):
  for mask in range(len(coef)):
   if mask&(1<<i):coef[mask]^=coef[mask^(1<<i)]
 def monomials(register):
  nodes={1<<i:q for i,q in enumerate(register)};undo=[]
  for mask in range(1,1<<len(register)):
   if mask in nodes:continue
   bit=mask&-mask;left=nodes[mask^bit];right=nodes[bit]
   target=b.alloc_qubits(1)[0];b.init_and(left,right,target)
   nodes[mask]=target;undo.append((left,right,target))
  return nodes,undo
 lo,lundo=monomials(address[:low_bits]);hi,hundo=monomials(address[low_bits:])
 one=b.alloc_qubits(1)[0];b.x(one)
 for mask,word in enumerate(coef):
  l=mask&((1<<low_bits)-1);h=mask>>low_bits
  while word:
   pos=(word&-word).bit_length()-1;b.push_condition(bits[pos])
   if l and h:b.cz(lo[l],hi[h])
   else:b.z(lo[l] if l else hi[h] if h else one)
   b.pop_condition();word&=word-1
 b.x(one);b.free(one)
 for left,right,target in reversed(hundo+lundo):
  b.del_and(left,right,target);b.free(target)
 for bit in bits:b.free(bit)

def repair(b,address,table,measurements,low_bits=4,anf=False):
 """Repair (-1)^(table[address] dot measurements), without output wires."""
 if anf:return repair_anf(b,address,table,measurements,low_bits)
 address=list(address);bits=list(measurements)
 low=address[:low_bits];high=address[low_bits:]
 rails=b.alloc_qubits(2);b.cx(low[-1],rails[0]);b.x(rails[0]);b.cx(low[-1],rails[1])
 current=list(rails);levels=[]
 for bit in reversed(low[:-1]):
  following=[];level=[]
  for parent in current:
   pair=b.alloc_qubits(2);lo,hi=pair
   b.init_and(parent,bit,hi);b.cx(parent,lo);b.cx(hi,lo)
   following.extend([lo,hi]);level.append((parent,bit,pair))
  levels.append(level);current=following
 def leaf(prefix,control):
  for j,rail in enumerate(current):
   word=table[(prefix<<low_bits)+j]
   while word:
    pos=(word&-word).bit_length()-1
    b.push_condition(bits[pos]);b.cz(control,rail);b.pop_condition()
    word&=word-1
 def walk(remaining,prefix,parent):
  if not remaining:leaf(prefix,parent);return
  bit=remaining[-1];rest=remaining[:-1]
  if parent is None:
   b.x(bit);walk(rest,prefix*2,bit);b.x(bit);walk(rest,prefix*2+1,bit)
  else:
   tmp=b.alloc_qubits(1)[0]
   b.x(bit);b.init_and(parent,bit,tmp);b.x(bit)
   walk(rest,prefix*2,tmp)
   b.cx(parent,tmp);walk(rest,prefix*2+1,tmp);b.cx(parent,tmp)
   b.x(bit);b.del_and(parent,bit,tmp);b.x(bit);b.free(tmp)
 walk(high,0,None)
 for level in reversed(levels):
  for parent,bit,pair in reversed(level):
   lo,hi=pair;b.cx(hi,lo);b.cx(parent,lo);b.del_and(parent,bit,hi);b.free(pair)
 b.cx(low[-1],rails[1]);b.x(rails[0]);b.cx(low[-1],rails[0]);b.free(rails)
 for bit in bits:b.free(bit)