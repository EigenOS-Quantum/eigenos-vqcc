"""Cuccaro MAJ/UMA prefix followed by a measured-carry Gidney suffix.

Trades clean carry workspace for additional Toffolis. New implementation,
Apache-2.0; circuit identities credited to Cuccaro et al. and Gidney.
"""
import signed_digit_lab as A

def add(b,a,t,cin=None,sub=False,borrowed=(),prefix=0):
 a,t=list(a),list(t);k=min(prefix,len(a),len(t)-1)
 if not k:return A.folded_gadd(b,a,t,cin,sub,borrowed=borrowed)
 if sub:
  for q in t:b.x(q)
 initial=None;available=list(borrowed)
 if cin is None:
  if available:cin=available.pop(0)
  else:initial=b.alloc_qubits(1)[0];cin=initial
 carry=cin
 for i in range(k):
  b.cx(a[i],t[i]);b.cx(a[i],carry);b.ccx(t[i],carry,a[i]);carry=a[i]
 A.folded_gadd(b,a[k:],t[k:],carry,borrowed=available)
 for i in reversed(range(k)):
  carry=cin if i==0 else a[i-1]
  b.ccx(t[i],carry,a[i]);b.cx(a[i],carry);b.cx(carry,t[i])
 if initial is not None:b.free(initial)
 if sub:
  for q in t:b.x(q)