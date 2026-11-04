"""Fast spot-check: simulate the candidate on edge + random x, report worst |err|/tol."""
import sys, math, json
import numpy as np
import kickmix as km
from invsqrt import verify_submission_invsqrt as iv

path = sys.argv[1]
nsh = int(sys.argv[2]) if len(sys.argv) > 2 else 256
spec = iv.ProblemSpecInvSqrt.for_n_p(10)
circuit = km.Circuit.from_file(path, format='kmb')
inputs, scratch = iv.validate_registers(circuit, spec)
print('num_qubits', circuit.num_qubits, 'registers', list(circuit.register_data))
rng = np.random.default_rng(20261026)
xs = rng.integers(1, spec.max_x + 1, nsh, dtype=np.uint64)
edges = [1, 2, 3, 4, 5, spec.max_x]
edges += [x for p in range(1, 23) for x in [2**p - 1, 2**p, 2**p + 1] if x <= spec.max_x]
xs[:len(edges)] = edges[:nsh]
sim = km.Simulator(batch_size=nsh, seed=20261026, debug_print=False)
sim.clear_for_shot()
sim.write_across_shots(inputs, iv.to_bits(xs, spec.width))
sim.do(circuit)
got_x = iv.from_bits(sim.read_across_shots(inputs))
assert np.array_equal(got_x, xs), 'x not restored'
if len(scratch):
    dirty = sim.read_across_shots(scratch).any(axis=1)
    print('scratch dirty shots:', int(dirty.sum()))
target, tol = iv.reference_values(spec, xs)
theta = np.array([iv.half_turns_to_units(sim.read_shot_phase(i)) for i in range(nsh)], dtype=np.uint64)
err = (theta - target).view(np.int64)
used = np.abs(err).view(np.uint64)
ratio = np.divide(used, tol, out=np.zeros(nsh, dtype=float), where=tol > 0)
order = np.argsort(-ratio)
print('worst 12 (x, ratio, err_turns, target_turns):')
for i in order[:12]:
    print('  x=%d ratio=%.4f err=%.6e turns target=%.9f' % (xs[i], ratio[i], err[i]/2**64, target[i]/2**64))
print('WORST RATIO over sample: %.4f' % ratio.max())
# also print the ratio of the phase to 1/sqrt(x) to detect a systematic scale error
import fractions
for i in order[:5]:
    t = theta[i] / 2**64
    true = 1.0 / math.sqrt(int(xs[i]))
    # find k with |t - k*true| minimal
    k = round(t / true) if true else 0
    print('  scale check x=%d: k=%d  k*1/sqrt(x)=%.9f  measured=%.9f' % (xs[i], k, k*true % 1.0, t))
