"""Sweep the stage_ref precision knobs (F2, F1, FYR, GY, DROP2) against the model.

For each config: rebuild the coefficient tables, report the model's worst relative
error (as a fraction of the 2^-24 tolerance) and the projected circuit cost.
"""
import sys, time, pickle, math, json
import numpy as np
import stage_ref as sr

CONFIGS = [
    # (F2, F1, FYR, GY, DROP2, tag)
    (10, 19, 26, 2, (5,),        'ref'),
    (9,  19, 26, 2, (5,),        'f2_9'),
    (10, 19, 26, 2, (5, 6),      'drop56'),
    (9,  19, 26, 2, (5, 6),      'f2_9_drop56'),
    (9,  19, 26, 2, (5, 6, 7),   'f2_9_drop567'),
    (10, 18, 26, 2, (5,),        'f1_18'),
    (9,  18, 26, 2, (5,),        'f2_9_f1_18'),
]

def rot_t(eps):
    return 0.56 * math.log2(1 / eps) + 5.3

out = {}
for (f2, f1, fyr, gy, drop, tag) in CONFIGS:
    t0 = time.time()
    cfg = sr.Cfg(f2, f1, fyr, gy, drop)
    tabs, worst = sr.build_tables(cfg)
    try:
        lay = sr.layout(cfg, tabs)
    except AssertionError as e:
        print(tag, 'LAYOUT FAIL', e, flush=True)
        continue
    # projection: qubits = 22 + 5 + w2 + w1 + LB + whi + (LB-1) carries during the y rows
    qubits = 22 + 5 + cfg.w2 + lay['w1'] + lay['LB'] + lay['whi'] + (lay['LB'] - 1)
    toff = None
    print(f'{tag}: secs={time.time()-t0:.1f} model_worst_ratio={worst*2**24:.4f} '
          f'w2={cfg.w2} w1={lay["w1"]} whi={lay["whi"]} rrows={len(cfg.rrow_list())} '
          f'qubits~{qubits}', flush=True)
    pickle.dump((tabs, lay), open(f'tables_{tag}.pkl', 'wb'))
    out[tag] = dict(f2=f2, f1=f1, fyr=fyr, gy=gy, drop=list(drop), worst=worst * 2**24,
                    qubits=qubits, secs=time.time() - t0)
json.dump(out, open('sweep_models.json', 'w'), indent=2)
print('DONE', flush=True)
