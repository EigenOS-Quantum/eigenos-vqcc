"""Build the direct-polynomial-phasing invsqrt circuit from stage_ref.py.

Usage: python build_ref.py OUT.kmb
"""
import sys, time, pickle
import numpy as np
import stage_ref as sr

OUT = sys.argv[1] if len(sys.argv) > 1 else 'invsqrt_ref.kmb'
TABLES = sys.argv[2] if len(sys.argv) > 2 else 'tables_ref.pkl'

cfg = sr.Cfg(sr.F2, sr.F1, sr.FYR, sr.GY, sr.DROP2)
tabs, lay = pickle.load(open(TABLES, 'rb'))
t0 = time.time()
c = sr.build_circuit(cfg, tabs, lay)
print('build secs', time.time() - t0, flush=True)
s = c.operation_statistics()
print('num_qubits', c.num_qubits, flush=True)
print('num_ops', len(c), flush=True)
print('reaction_depth', c.reaction_depth(), flush=True)
for n in dir(s):
    if not n.startswith('_'):
        print('  stat', n, getattr(s, n), flush=True)
c.to_file(OUT, format='kmb')
print('wrote', OUT, flush=True)
