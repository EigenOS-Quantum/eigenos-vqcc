# Attribution: Sumit Chongder, Apache-2.0 as published.
# https://www.kaggle.com/code/sumitchongder/notebook2f196e646b
# Read-only source downloaded from latest version 2. Kirill's v9 cites v1.
# This isolated lab regenerates the circuit from readable source; no binaries or
# remote notebook outputs are inputs. Our added exact integer certificate and
# reporting helpers and memory-schedule adaptations follow the original generator.
"""Builds an optimized kickmix circuit for the invsqrt benchmark (Benchmark I).

|x>|0> -> exp(2 pi i / sqrt(x)) |x>|0>,   x in [1, 3133452], 22-bit register 'x'.

Design (all arithmetic exactly mirrored by the numpy model below):
  1. Normalize x by single-bit binary stages (16, 8, 4, 2, 1) into M = x_norm / 2^21 in [1, 2);
     flags f0..f4 hold the shift count s' in binary.  e = f0 (parity), s = s' >> 1.
     1/sqrt(x) = 2^(s-10) * y,  y = 2^((e-1)/2) / sqrt(M)  in (0.5, 1].
  2. One 256-entry QROM indexed by (7 mantissa bits, e) XORs quadratic coefficients directly into
     the working registers (no separate coefficient copies).
  3. Centered signed-digit Horner: delta_c = sum_i (2 d_i - 1) 2^(i-22) over the 14 low bits.
     R = K1 - C2*delta_c,  y = K0 - R*delta_c.  Each row is an UNcontrolled Gidney addition
     wrapped in CNOT flips (Y - A = ~(~Y + A)), with a rounding carry-in.
  4. The y register is split: rows only touch a 21-bit low register L; the constant high part
     sits in a separate register and the overflow bit is merged in before phasing.
  5. Binary de-normalization (shift by s), one Z_POW per bit, then exact mirror uncompute.
     Lookup uncompute is measurement based (del_lookup); normalization flags are cleared by HMR
     with classically conditioned phase fixups.
Usage: python signed_digit_lab.py OUT.kmb [--baseline] (requires kickmix and NumPy)
"""
import sys, math
from fractions import Fraction
import numpy as np
import kickmix as km

W = 22; MB = 21; DB = 14; NSEG = 128
F2, F1, FYR, GY, DROP2 = 10, 19, 26, 2, (5,)     # precision configuration (verified)

# ----------------------------------------------------------------- numpy model / tables
def fitc(lo, hi, mid, scale, deg=2, iters=80):
    f = lambda M: scale / np.sqrt(M)
    d = np.linspace(lo - mid, hi - mid, 3001)
    A = np.vander(d, deg + 1, increasing=True)
    w = np.sqrt(mid + d) / scale
    wt = np.ones_like(d)
    for _ in range(iters):                       # Lawson iterations -> weighted minimax
        sw = w * np.sqrt(wt)
        coef = np.linalg.lstsq(A * sw[:, None], f(mid + d) * sw, rcond=None)[0]
        err = np.abs((A @ coef - f(mid + d)) * w)
        wt = wt * err; wt /= wt.sum()
    return coef

class Cfg:
    def __init__(self, f2, f1, fyr, gy, drop2=()):
        self.f2, self.f1, self.fyr, self.gy = f2, f1, fyr, gy
        self.fy = fyr + gy
        self.w2 = f2 - 1
        self.sh2 = [f2 + 22 - i - f1 for i in range(DB)]
        self.sh1 = [f1 + 22 - i - self.fy for i in range(DB)]
        self.drop2 = set(drop2)
    def rrow_list(self):
        return [i for i in reversed(range(DB)) if i not in self.drop2 and self.sh2[i] < self.w2]

def rd(v, s):
    if s < 0: return v << (-s)
    r = v >> s
    if s >= 1: r = r + ((v >> (s - 1)) & 1)
    return r

def pipeline(cfg, K2, K1, d):
    sig = [2 * ((d >> i) & 1) - 1 for i in range(DB)]
    R = np.full_like(d, K1)
    for i in cfg.rrow_list():
        R = R - sig[i] * rd(K2, cfg.sh2[i])
    Q = np.zeros_like(d)
    for i in reversed(range(DB)):
        Q = Q + sig[i] * rd(R, cfg.sh1[i])
    return R, Q

def build_tables(cfg, search=2):
    tabs = {}; worst = 0
    dmid = (2**DB - 1) / 2**(MB + 1)
    d = np.arange(2**DB, dtype=np.int64)
    g = cfg.gy
    for e in (0, 1):
        scale = 2**((e - 1) / 2)
        for a in range(NSEG):
            lo = 1 + a * 2.0**(DB - MB); mid = lo + dmid
            c = fitc(lo, lo + 2.0**(DB - MB), mid, scale)
            C1, C2 = -c[1], c[2]
            M = lo + d * 2.0**-MB
            fM = scale / np.sqrt(M); tgt = fM * 2.0**cfg.fy; w = 1 / fM
            K2c = int(round(C2 * 2**cfg.f2)); K1c = int(round(C1 * 2**cfg.f1))
            best = None
            for K2 in range(K2c - 1, K2c + 2):
                for K1 in range(K1c - search, K1c + search + 1):
                    R, Q = pipeline(cfg, K2, K1, d)
                    def mx(K0):
                        Y = ((K0 - Q) >> g) << g
                        return float(np.max(np.abs(Y - tgt) * w))
                    t = tgt + Q
                    a_, b_ = math.floor(t.min()), math.ceil(t.max())
                    while b_ - a_ > 2:
                        m1 = a_ + (b_ - a_) // 3; m2 = b_ - (b_ - a_) // 3
                        if mx(m1) < mx(m2): b_ = m2
                        else: a_ = m1
                    for K0 in range(a_, b_ + 1):
                        v = mx(K0) / 2.0**cfg.fy
                        if best is None or v < best[0]: best = (v, K2, K1, K0)
            tabs[(e, a)] = best[1:]
            worst = max(worst, best[0])
    return tabs, worst

def layout(cfg, tabs, LB=21, S=20):
    d = np.arange(2**DB, dtype=np.int64)
    assert max(t[0] for t in tabs.values()) < (1 << cfg.w2)
    Rmax = 0; per = {}; Ymax = 0
    for key, (K2, K1, K0) in tabs.items():
        R, Q = pipeline(cfg, K2, K1, d)
        assert R.min() >= 0
        Rmax = max(Rmax, int(R.max()), K1)
        per[key] = (int(Q.min()), int(Q.max()))
        Ymax = max(Ymax, K0 - per[key][0])
    w1 = Rmax.bit_length()
    lo_tab, hi_tab = {}, {}
    for key, (K2, K1, K0) in tabs.items():
        qmin, qmax = per[key]
        base = K0 % (1 << S); j = 0
        while base + j * (1 << S) - qmax < 0: j += 1
        k0lo = base + j * (1 << S)
        assert k0lo - qmin < (1 << LB), 'layout infeasible'
        lo_tab[key] = k0lo; hi_tab[key] = (K0 - k0lo) >> S
        assert hi_tab[key] >= 0
    whi = max(max(hi_tab.values()).bit_length(), 1)
    return dict(w1=w1, LB=LB, S=S, whi=whi, lo=lo_tab, hi=hi_tab)

# ----------------------------------------------------------------- circuit pieces
def and_all_into(b, controls, target):
    k = len(controls)
    if k == 1: b.cx(controls[0], target); return
    if k == 2: b.ccx(controls[0], controls[1], target); return
    anc = b.alloc_qubits(k - 2)
    b.init_and(controls[0], controls[1], anc[0])
    for j in range(1, k - 2): b.init_and(anc[j - 1], controls[j + 1], anc[j])
    b.ccx(anc[k - 3], controls[k - 1], target)
    for j in reversed(range(1, k - 2)): b.del_and(anc[j - 1], controls[j + 1], anc[j])
    b.del_and(controls[0], controls[1], anc[0])
    b.free(anc)

def phase_all(b, controls):
    k = len(controls)
    if k == 1: b.z(controls[0]); return
    if k == 2: b.cz(controls[0], controls[1]); return
    anc = b.alloc_qubits(k - 2)
    b.init_and(controls[0], controls[1], anc[0])
    for j in range(1, k - 2): b.init_and(anc[j - 1], controls[j + 1], anc[j])
    b.cz(anc[k - 3], controls[k - 1])
    for j in reversed(range(1, k - 2)): b.del_and(anc[j - 1], controls[j + 1], anc[j])
    b.del_and(controls[0], controls[1], anc[0])
    b.free(anc)

NSTAGES = [(4, 16), (3, 8), (2, 4), (1, 2), (0, 1)]

def normalize(b, x, f):
    for (k, d) in NSTAGES:
        top = x[W - d:W]
        if d == 1:
            b.cx(x[W - 1], f[0]); b.x(f[0])
        else:
            b.x(top); and_all_into(b, list(top), f[k]); b.x(top)
        for i in reversed(range(0, W - d)): b.cswap(f[k], x[i], x[i + d])

def unnormalize(b, x, f):
    for (k, d) in reversed(NSTAGES):
        for i in range(0, W - d): b.cswap(f[k], x[i], x[i + d])
        top = x[W - d:W]
        if d == 1:
            b.x(f[0]); b.cx(x[W - 1], f[0])
        else:
            m = b.alloc_bits(1)[0]
            b.hmr(f[k], m)
            b.push_condition(m)                     # fixup runs on half the shots on average
            b.x(top); phase_all(b, list(top)); b.x(top)
            b.pop_condition()
            b.free(m)

def gadd(b, a, t, cin=None, sub=False):
    """t += a + cin (or t -= a + cin), Gidney adder: len(t)-1 Toffolis, uncompute by HMR."""
    a = list(a); t = list(t); o = len(a); n = len(t)
    assert o <= n
    if sub: b.x(km.array(t))
    c = b.alloc_qubits(n - 1) if n > 1 else km.array([])
    def C(i): return cin if i == 0 else c[i - 1]
    for i in range(0, n - 1):
        if i == 0 and cin is None:
            if o: b.init_and(a[0], t[0], C(1))
        elif i < o:
            b.cx(C(i), a[i]); b.cx(C(i), t[i]); b.init_and(a[i], t[i], C(i + 1)); b.cx(C(i), C(i + 1))
        else:
            b.init_and(C(i), t[i], C(i + 1))
    if n - 1 < o: b.cx(a[n - 1], t[n - 1])
    if n > 1 or cin is not None: b.cx(C(n - 1), t[n - 1])
    for i in reversed(range(0, n - 1)):
        if i == 0 and cin is None:
            if o: b.del_and(a[0], t[0], C(1)); b.cx(a[0], t[0])
        elif i < o:
            b.cx(C(i), C(i + 1)); b.del_and(a[i], t[i], C(i + 1)); b.cx(C(i), a[i]); b.cx(a[i], t[i])
        else:
            b.del_and(C(i), t[i], C(i + 1)); b.cx(C(i), t[i])
    if n > 1: b.free(c)
    if sub: b.x(km.array(t))

def shift_stages(b, f, reg, L, inverse):
    stages = [(1, 1), (2, 2), (3, 4), (4, 8)]
    occ = []; o = L
    for (k, d) in stages: occ.append(o); o = min(o + d, len(reg))
    seq = list(enumerate(stages))
    if not inverse:
        for idx, (k, d) in seq:
            for i in reversed(range(0, occ[idx])):
                if i + d < len(reg): b.cswap(f[k], reg[i], reg[i + d])
    else:
        for idx, (k, d) in reversed(seq):
            for i in range(0, occ[idx]):
                if i + d < len(reg): b.cswap(f[k], reg[i], reg[i + d])

def build_circuit(cfg, tabs, lay, adder=None):
    # The default preserves the public generator exactly. An injected adder
    # supports isolated, explicitly tested memory experiments.
    if adder is None: adder=gadd
    w2, w1, LB, S, whi = cfg.w2, lay['w1'], lay['LB'], lay['S'], lay['whi']
    gy, fy = cfg.gy, cfg.fy
    b = km.CircuitBuilder()
    x = b.create_quantum_register(W, name='x')
    f = b.alloc_qubits(5)
    c2 = b.alloc_qubits(w2); R = b.alloc_qubits(w1); Lr = b.alloc_qubits(LB); Yh = b.alloc_qubits(whi)
    tgt = km.array(list(Lr) + list(R) + list(c2) + list(Yh))
    table = [0] * 256
    for (e, a), (K2, K1, K0) in tabs.items():
        table[a + 128 * e] = lay['lo'][(e, a)] | (K1 << LB) | (K2 << (LB + w1)) | (lay['hi'][(e, a)] << (LB + w1 + w2))
    addr = km.array(list(x[14:21]) + [f[0]])
    delta = x[0:DB]
    def rrows(inverse):
        seq = cfg.rrow_list()
        if inverse: seq = list(reversed(seq))
        for i in seq:
            sh = cfg.sh2[i]
            if sh >= 0: off = c2[sh:w2]; t = R[0:w1]; cin = c2[sh - 1] if sh >= 1 else None
            else: off = c2[0:w2]; t = R[-sh:w1]; cin = None
            b.cx(delta[i], t); adder(b, off, t, cin, sub=inverse); b.cx(delta[i], t)
    def yrows(inverse):
        seq = list(reversed(range(DB)))
        if inverse: seq.reverse()
        for i in seq:
            sh = cfg.sh1[i]; assert 0 <= sh < w1
            t = Lr[0:LB]; cin = R[sh - 1] if sh >= 1 else None
            b.cx(delta[i], t); adder(b, R[sh:w1], t, cin, sub=inverse); b.cx(delta[i], t)
    normalize(b, x, f)
    b.init_lookup(table=table, address=addr, target=tgt)
    rrows(False); yrows(False)
    ext = b.alloc_qubits(10)
    if LB > S: adder(b, Lr[S:LB], Yh)
    Cx = km.array(list(Lr[gy:S]) + list(Yh) + list(ext))
    shift_stages(b, f, Cx, S - gy + whi, False)
    for j in range(len(Cx)):
        e = gy + j - fy - 10                       # bit weight 2^e turns
        if e < 0: b.z_pow(Cx[j], Fraction(2)**(e + 1))
    shift_stages(b, f, Cx, S - gy + whi, True)
    if LB > S: adder(b, Lr[S:LB], Yh, sub=True)
    b.free(ext)
    yrows(True); rrows(True)
    b.del_lookup(table=table, address=addr, target=tgt)
    b.free(tgt)
    unnormalize(b, x, f)
    b.free(f)
    return b.finish_circuit()

def main(out):
    cfg = Cfg(F2, F1, FYR, GY, DROP2)
    tabs, worst = build_tables(cfg)
    print(f'model worst relative error / 2^-24 = {worst * 2**24:.3f}')
    lay = layout(cfg, tabs)
    c = build_circuit(cfg, tabs, lay)
    s = c.operation_statistics()
    print('qubits', c.num_qubits, 'toffoli(static)', s.num_toffoli_like,
          'rotations', s.num_z_pow(min_clifford_hierarchy_level=4))
    c.to_file(out, format='kmb')
    print('wrote', out)


def selected_cfg():
    return Cfg(F2,F1,FYR,GY,DROP2)


def config_record(cfg):
    return dict(f2=cfg.f2,f1=cfg.f1,fyr=cfg.fyr,gy=cfg.gy,drop2=sorted(cfg.drop2))


def load_or_build_tables(path=None):
    """Regenerate open-source coefficients, optionally retaining a local cache."""
    import json
    from pathlib import Path
    cfg=selected_cfg()
    path=Path(path) if path else None
    if path and path.exists():
        saved=json.loads(path.read_text())
        assert saved['config']==config_record(cfg)
        rows=saved['rows']
        assert len(rows)==256 and all(len(row)==3 for row in rows)
        tabs={(i//128,i%128):tuple(map(int,row)) for i,row in enumerate(rows)}
        return cfg,tabs,saved['normalized_worst_relative_error']
    tabs,worst=build_tables(cfg)
    if path:
        path.write_text(json.dumps({'source':'Sumit Chongder open generator, latest v2',
            'config':config_record(cfg),'normalized_worst_relative_error':worst,
            'rows':[tabs[(e,a)] for e in range(2) for a in range(128)]},indent=2))
    return cfg,tabs,worst


def integer_model(xs,cfg,tabs):
    """Exact emitted arithmetic in units 2^-(cfg.fy+10) turns, before mod 1."""
    xs=np.asarray(xs,dtype=np.int64)
    if not ((xs>=1)&(xs<=3133452)).all():
        raise ValueError('The supported competition domain is x=1..3133452')
    # All inputs fit exactly in float64; frexp gives the exact binary exponent.
    shifts=21-(np.frexp(xs)[1].astype(np.int64)-1)
    norm=xs << shifts
    assert ((norm >> 21)==1).all(), 'Normalized top-bit borrowing requires x[21]=1'
    parity=shifts&1
    index=((norm >> 14)&127)+128*parity
    table=np.asarray([tabs[(e,a)] for e in range(2) for a in range(128)],dtype=np.int64)
    K2,K1,K0=(table[index,j] for j in range(3))
    d=norm&((1 << DB)-1)
    signs=[2*((d >> i)&1)-1 for i in range(DB)]
    R=K1.copy()
    for i in cfg.rrow_list():
        R-=signs[i]*rd(K2,cfg.sh2[i])
    Q=np.zeros_like(xs)
    for i in reversed(range(DB)):
        Q+=signs[i]*rd(R,cfg.sh1[i])
    Y=((K0-Q) >> cfg.gy) << cfg.gy
    if (R<0).any() or (Y<0).any():
        raise OverflowError('An unsigned intermediate is negative')
    return Y << (shifts >> 1)


def exhaustive_certificate(cfg,tabs,chunk_size=131072):
    """Every promised basis input, exact integer target and tolerance.

    This is an arithmetic certificate. Ancillas, restored inputs and phase
    feed-forward require fresh circuit simulation and the official verifier.
    """
    output_fraction=cfg.fy+10
    worst_ratio,worst_x,min_margin=0.,0,1 << 64
    for start in range(1,3133453,chunk_size):
        xs=np.arange(start,min(start+chunk_size,3133453),dtype=np.int64)
        values=integer_model(xs,cfg,tabs).astype(np.uint64)
        phase=values << np.uint64(64-output_fraction)
        roots=[math.isqrt((1 << 130)//int(x)) for x in xs]
        target=np.array([((r+1) >> 1)&((1 << 64)-1) for r in roots],dtype=np.uint64)
        tolerance=np.array([min(r >> 25,1 << 63) for r in roots],dtype=np.uint64)
        error=np.abs((phase-target).view(np.int64)).view(np.uint64)
        ratio=error/tolerance
        i=int(np.argmax(ratio))
        if float(ratio[i])>worst_ratio:
            worst_ratio,worst_x=float(ratio[i]),int(xs[i])
        if (error>tolerance).any():
            i=int(np.flatnonzero(error>tolerance)[0])
            return {'pass':False,'first_bad_x':int(xs[i]),'ratio':float(ratio[i])}
        min_margin=min(min_margin,int((tolerance-error).min()))
    return {'pass':True,'tested_inputs':3133452,'worst_ratio':worst_ratio,
            'worst_x':worst_x,'min_margin_units':min_margin,
            'phase_fraction_bits':output_fraction}


def estimated_resources(circuit,certificate):
    """Model-based cost; full unchanged official verification remains required."""
    assert certificate['pass'] and certificate['min_margin_units']>0
    stats=circuit.operation_statistics()
    rotations=int(stats.num_z_pow(min_clifford_hierarchy_level=4))
    epsilon=math.pi*(certificate['min_margin_units']/2**64)/rotations
    per_rotation=0.56*math.log2(1/epsilon)+5.3
    static_toffoli=int(stats.num_toffoli_like)
    # Four X-basis flag measurements independently activate phase_all on half
    # the shots. Its 16,8,4,2-control paths have 14+6+2+0 Toffolis in total.
    normalization_discount=sum(max(0,d-2) for _,d in NSTAGES if d>1)/2
    expected_toffoli=static_toffoli-normalization_discount
    t_like=int(stats.num_t_like)
    extra=(t_like+rotations*per_rotation)/4
    return {'qubits':circuit.num_qubits,'static_toffoli':static_toffoli,
            'expected_mean_toffoli':expected_toffoli,'t_like':t_like,
            'rotations':rotations,'rotation_epsilon':epsilon,
            'estimated_expected_cost':circuit.num_qubits*(expected_toffoli+extra),
            'static_cost_upper_estimate':circuit.num_qubits*(static_toffoli+extra),
            'full_official_verification_required':True}




# ---- Our isolated phase scheduling, folded carry and borrowed workspace ----
def folded_gadd(b,a,t,cin=None,sub=False,borrowed=()):
    a,t=list(a),list(t)
    o,n=len(a),len(t)
    assert o<=n and n>=1
    if sub:
        for q in t:b.x(q)
    if n==1:
        if o:b.cx(a[0],t[0])
        if cin is not None:b.cx(cin,t[0])
        if sub:
            for q in t:b.x(q)
        return
    borrowed=list(borrowed)[:max(0,n-2)]
    count=max(0,n-2-len(borrowed))
    allocated=b.alloc_qubits(count) if count else []
    c=borrowed+list(allocated)
    def C(i):return cin if i==0 else c[i-1]
    for i in range(n-2):
        if i==0 and cin is None:
            if o:b.init_and(a[0],t[0],C(1))
        elif i<o:
            b.cx(C(i),a[i]);b.cx(C(i),t[i])
            b.init_and(a[i],t[i],C(i+1));b.cx(C(i),C(i+1))
        else:
            b.init_and(C(i),t[i],C(i+1))
    i=n-2
    carry=C(i)
    if carry is None:
        if i<o:
            b.ccx(a[i],t[i],t[-1]);b.cx(a[i],t[i])
    elif i<o:
        b.cx(carry,a[i]);b.cx(carry,t[i])
        b.ccx(a[i],t[i],t[-1]);b.cx(carry,t[-1])
        b.cx(carry,a[i]);b.cx(a[i],t[i])
    else:
        b.ccx(carry,t[i],t[-1]);b.cx(carry,t[i])
    if n-1<o:b.cx(a[n-1],t[n-1])
    for i in reversed(range(n-2)):
        if i==0 and cin is None:
            if o:b.del_and(a[0],t[0],C(1));b.cx(a[0],t[0])
        elif i<o:
            b.cx(C(i),C(i+1));b.del_and(a[i],t[i],C(i+1))
            b.cx(C(i),a[i]);b.cx(a[i],t[i])
        else:
            b.del_and(C(i),t[i],C(i+1));b.cx(C(i),t[i])
    if count:b.free(allocated)
    if sub:
        for q in t:b.x(q)


def truth_table_check(max_width=6,borrowed_count=0):
    class Bits:
        def __init__(self):self.v=[]
        def alloc_qubits(self,n):
            ids=list(range(len(self.v),len(self.v)+n));self.v.extend([0]*n);return ids
        def x(self,q):self.v[q]^=1
        def cx(self,a,t):self.v[t]^=self.v[a]
        def ccx(self,a,b,t):self.v[t]^=self.v[a]&self.v[b]
        def init_and(self,a,b,t):
            assert self.v[t]==0
            self.v[t]=self.v[a]&self.v[b]
        def del_and(self,a,b,t):
            assert self.v[t]==(self.v[a]&self.v[b])
            self.v[t]=0
        def free(self,reg):assert not any(self.v[q] for q in reg)
        def put(self,reg,value):
            for i,q in enumerate(reg):self.v[q]=(value >> i)&1
        def read(self,reg):return sum(self.v[q] << i for i,q in enumerate(reg))
    count=0
    for n in range(1,max_width+1):
        for m in range(n+1):
            for a in range(1 << m):
                for value in range(1 << n):
                    for cin_value in (None,0,1):
                        for sub in (False,True):
                            b=Bits();areg=b.alloc_qubits(m);target=b.alloc_qubits(n)
                            cin=b.alloc_qubits(1)[0] if cin_value is not None else None
                            if cin is not None:b.v[cin]=cin_value
                            b.put(areg,a);b.put(target,value)
                            borrowed=b.alloc_qubits(borrowed_count)
                            folded_gadd(b,areg,target,cin,sub,borrowed=borrowed)
                            delta=a+(cin_value or 0)
                            expected=(value-delta if sub else value+delta) % (1 << n)
                            assert b.read(target)==expected,(n,m,a,value,cin_value,sub)
                            assert b.read(areg)==a
                            assert cin is None or b.v[cin]==cin_value
                            assert not any(b.v[q] for q in borrowed)
                            count+=1
    return count


def build_split_circuit(cfg,tabs,lay,adder=None,borrow_top=False):
    if adder is None:adder=gadd
    w2,w1,LB,S,whi=cfg.w2,lay['w1'],lay['LB'],lay['S'],lay['whi']
    b=km.CircuitBuilder()
    x=b.create_quantum_register(W,name='x')
    flags=b.alloc_qubits(5)
    normalize(b,x,flags)
    # Every promised positive input normalizes to x[21]=1. The arithmetic
    # address uses x[14:21] and delta x[:14], so this wire is idle in the core.
    if borrow_top:
        b.x(x[-1])
        raw_adder=adder
        def adder(builder,a,t,cin=None,sub=False):
            return raw_adder(builder,a,t,cin,sub,borrowed=(x[-1],))
    c2=b.alloc_qubits(w2)
    R=b.alloc_qubits(w1)
    Lr=b.alloc_qubits(LB)
    Yh=b.alloc_qubits(whi)
    remaining=km.array(list(Lr)+list(R)+list(c2))
    target=km.array(list(remaining)+list(Yh))
    table=[0]*256
    rest_table=[0]*256
    high_table=[0]*256
    for (e,a),(K2,K1,K0) in tabs.items():
        idx=a+128*e
        rest_table[idx]=lay['lo'][(e,a)] | (K1 << LB) | (K2 << (LB+w1))
        high_table[idx]=lay['hi'][(e,a)]
        table[idx]=rest_table[idx] | (high_table[idx] << (LB+w1+w2))
    address=km.array(list(x[14:21])+[flags[0]])
    delta=x[:DB]
    def rrows(inverse):
        seq=cfg.rrow_list()
        if inverse:seq=list(reversed(seq))
        for i in seq:
            sh=cfg.sh2[i]
            if sh>=0:off=c2[sh:w2];t=R[:w1];cin=c2[sh-1] if sh>=1 else None
            else:off=c2[:w2];t=R[-sh:w1];cin=None
            b.cx(delta[i],t);adder(b,off,t,cin,sub=inverse);b.cx(delta[i],t)
    def yrows(inverse):
        seq=list(reversed(range(DB)))
        if inverse:seq.reverse()
        for i in seq:
            sh=cfg.sh1[i]
            assert 0<=sh<w1
            cin=R[sh-1] if sh>=1 else None
            b.cx(delta[i],Lr);adder(b,R[sh:w1],Lr,cin,sub=inverse);b.cx(delta[i],Lr)
    def phase(reg,base_bit):
        ext=b.alloc_qubits(10)
        word=km.array(list(reg)+list(ext))
        shift_stages(b,flags,word,len(reg),False)
        for j in range(len(word)):
            exponent=base_bit+j-cfg.fy-10
            if exponent<0:b.z_pow(word[j],Fraction(2)**(exponent+1))
        shift_stages(b,flags,word,len(reg),True)
        b.free(ext)
    b.init_lookup(table=table,address=address,target=target)
    phase(Yh,S)
    b.del_lookup(table=high_table,address=address,target=Yh)
    b.free(Yh)
    rrows(False)
    yrows(False)
    phase(Lr[cfg.gy:LB],cfg.gy)
    yrows(True)
    rrows(True)
    b.del_lookup(table=rest_table,address=address,target=remaining)
    b.free(remaining)
    if borrow_top:b.x(x[-1])
    unnormalize(b,x,flags)
    b.free(flags)
    return b.finish_circuit()


def build_selected(cfg,tabs,lay=None):
    """Selected unchanged-Sumit model with split high phase and 93-qubit schedule.

    The normalized input's top bit is known to be one throughout the core;
    it is temporarily zeroed for a carry wire and restored before unnormalizing.
    Every call regenerates a circuit from source and ordinary numeric tables.
    """
    if lay is None:lay=layout(cfg,tabs)
    return build_split_circuit(cfg,tabs,lay,adder=folded_gadd,borrow_top=True)


def selected_descriptor():
    return {
        'variant':'sumit_split_folded_borrow',
        'source_author':'Sumit Chongder',
        'source_url':'https://www.kaggle.com/code/sumitchongder/notebook2f196e646b?scriptVersionId=361357149',
        'source_download':'Latest v2 readable generator; regenerated baseline canonical bytes match cited v1 report',
        'license_as_published':'Apache-2.0',
        'coefficient_changes':'None; original Sumit Cfg(10,19,26,2,(5,)) and generated coefficient table',
        'own_changes':[
            'Allocate coefficient registers after normalization',
            'Phase constant high word and measurement-unlookup it before Horner arithmetic',
            'Phase the low accumulator including its overflow bit separately; remove high/low merge adders',
            'Fold final ripple carry directly into highest target bit, including the rounding carry-in',
            'Borrow normalized x[21] as a clean carry wire; restore its value before unnormalization'],
        'baseline_canonical_sha256':'f19a8207e282859f663abe7f655b06eb3224d32ac99fbf899e1422b3795ca0be',
        'selected_canonical_sha256':'85611d22c524a5e982f2beafd11e32e6d39c86e174d3438734ff5a088679090a',
        'measured_counts':{'qubits':93,'static_toffoli':1582,'rotations':44},
        'expected_mean_toffoli':1571.0,
        'estimated_cost':175203.2709288877,
        'official_full_verification':'Required separately; no arithmetic certificate substitutes for it'}


def comparison_report(cfg,tabs,certificate,lay=None):
    """Measured circuit counts and model-based estimates, without executing verification."""
    if lay is None:lay=layout(cfg,tabs)
    baseline=build_circuit(cfg,tabs,lay)
    selected=build_selected(cfg,tabs,lay)
    return {'baseline':estimated_resources(baseline,certificate),
            'selected':estimated_resources(selected,certificate),
            'selected_descriptor':selected_descriptor()}


def cli():
    import argparse
    import json
    from pathlib import Path
    parser = argparse.ArgumentParser(description='Generate the credited signed-digit circuit and memory-schedule adaptation.')
    parser.add_argument('output', nargs='?', default='invsqrt.kmb')
    parser.add_argument('--baseline', action='store_true')
    args = parser.parse_args()
    cfg, tabs, _ = load_or_build_tables()
    certificate = exhaustive_certificate(cfg, tabs)
    if not certificate['pass']:
        raise ArithmeticError(certificate)
    lay = layout(cfg, tabs)
    circuit = build_circuit(cfg, tabs, lay) if args.baseline else build_selected(cfg, tabs, lay)
    circuit.to_file(args.output, format='kmb')
    report = estimated_resources(circuit, certificate)
    report['arithmetic_certificate'] = certificate
    report['variant'] = 'sumit_baseline' if args.baseline else selected_descriptor()['variant']
    Path(args.output + '.resources.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    cli()