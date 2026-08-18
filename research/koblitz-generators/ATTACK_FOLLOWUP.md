# Attack-oriented follow-up

## Outcome

Two previously incomplete attack-oriented experiments are now reproducible. Neither
found evidence that the historical-style generator is easier than uniform controls.

## Process-isolated Semaev/Gröbner campaign

`scripts/run_blinded_groebner.py` randomizes opaque job identifiers and runs exactly one
Sage/Singular ideal per subprocess. The parent imposes a hard wall-clock timeout, so a
stuck C call cannot stall the campaign. It supports f3/f4, multiple monomial orders,
parallel workers, complete matched-curve selection, and exact `[limit+1]P` probes for
censored relation scans. `sage/groebner_worker.py` sees no generator-class label.

The initial 36 decomposition-conditioned f4 jobs all completed. Every ideal was
non-unit and had maximum Gröbner-basis degree 2 or 3. A 15-second censored-target run
appeared heavily timed out, but a matched 10-curve/30-job replication with a 30-second
cap completed all jobs. With four concurrent Sage processes, typical worker wall time
was about 10–15 seconds and was dominated by process/import/contention overhead.

This corrects the earlier interpretation: the observed timeouts do not currently
establish a Singular heavy tail, much less a base-class effect. Longer campaigns should
use a timeout comfortably above measured startup time, preserve complete curve/base
blocks, and compare worker-internal time rather than total process startup time.

Principal outputs:

- `results/groebner_isolated_initial.jsonl`
- `results/groebner_isolated_initial_analysis.json`
- `results/groebner_matched_10.jsonl`
- `results/groebner_matched_10_analysis.json`

## Deduplicated GLV coefficient-box campaign

`scripts/glv_box_scan.py` evaluates

`u*P + v*phi(P) = [u + v*lambda]P`

over a bounded coefficient box. It orients lambda against the recorded beta map and
deduplicates the resulting scalar set. This matters because the GLV lattice and scalar
set are curve-level objects; only their image coordinates are base-conditioned.

On 100 curves, ten bases per curve, and the `[-16,16]^2` box, five of six exploratory
comparisons were null. Historical bases initially showed a slightly *higher* minimum
x-coordinate popcount than eight controls: +0.289 bits, exchangeability p=0.00784.
This is opposite the hypothesized easier/sparser direction.

The same metric was immediately preregistered informally and repeated on 100 fresh
curves. It changed sign to -0.018 bits with p=0.868. Every other replication comparison
was also null (all p>=0.18). The anomaly therefore failed replication and should be
treated as ordinary multiple-testing variation.

### Expanded speculative search

The scanner was subsequently optimized to walk the two-dimensional point grid using
exact additions rather than repeating a scalar multiplication for every coefficient.
Its metrics were cross-checked against the scalar engine; x-coordinate witnesses can
differ by sign because `x(P)=x(-P)`, but all minima agree. The optimized engine was
about nine times faster in the smoke benchmark.

Two fresh 200-curve blocks were searched over `[-128,128]^2`: 66,048 nonzero scalar
samples per base, ten bases per curve, or 264,192,000 coefficient/base observations in
total. In the discovery block, historical minimum centered x was nominally 0.289 log2
units lower than the eight-control mean (p=0.0283). This did not survive correction for
six exploratory tests. In the pre-separated replication block, the effect reversed to
+0.029 (p=0.831). The combined 400-curve effect was -0.130 (p=0.171). Every combined
comparison was null; historical p-values were 0.171, 0.858, and 0.826 for centered-x,
popcount, and bit-length minima respectively.

This is the second nominal orbit anomaly to fail an immediate fresh-data replication.
It strengthens the interpretation that repeated uncorrected testing will occasionally
produce small p-values, while the historical generator class remains exchangeable with
uniform controls under these observables.

Expanded outputs:

- `results/glv_box_b128_discovery.jsonl`
- `results/glv_box_b128_discovery_analysis.json`
- `results/glv_box_b128_replication.jsonl`
- `results/glv_box_b128_replication_analysis.json`
- `results/glv_box_b128_combined_analysis.json`

Principal outputs:

- `results/glv_box_b16_initial.jsonl`
- `results/glv_box_b16_initial_analysis.json`
- `results/glv_box_b16_replication.jsonl`
- `results/glv_box_b16_replication_analysis.json`

## Scaling commands

Run a complete matched f4 campaign (adjust workers to physical RAM and CPU capacity):

```bash
python3 scripts/run_blinded_groebner.py \
  --relations results/relations_f4.jsonl --corpus data/corpus.jsonl \
  --output results/groebner_matched_100.jsonl --include-censored \
  --max-curves 100 --orders degrevlex,deglex,lex \
  --timeout-seconds 120 --workers 8
python3 scripts/analyze_groebner.py \
  --input results/groebner_matched_100.jsonl \
  --output results/groebner_matched_100_analysis.json
```

Increase the GLV box on a fresh block:

```bash
python3 scripts/glv_box_scan.py --start 200 --count 200 --bound 64 \
  --output results/glv_box_b64.jsonl
python3 scripts/analyze_glv_box.py --input results/glv_box_b64.jsonl \
  --output results/glv_box_b64_analysis.json
```

The next genuinely distinct attack model should not merely enlarge these null tests.
The best candidate is a formally specified small-root system in which the unknown is
part of an ECDLP instance and the short `x(H)` changes an explicit lattice bound. Merely
encoding the already-public low coordinate, without connecting it to the secret scalar,
does not constitute an attack hypothesis.

## Actual-curve LLL coordinate-relation search

`sage/lll_coordinate_relations.py` tests the four real SEC curves rather than small
analogues. For each point P and dimension m it computes x(P) through x([m]P), constructs
the integer lattice for

`sum(c_i * x([i]P)) = 0 mod p`,

and uses LLL to find a short exact coefficient vector. Every saved witness is checked
modulo p before it is emitted. The primary statistic is the log2 Euclidean coefficient
norm minus the generic determinant scale `log2(p)/m`.

The preregistered discovery run used m=6,8,10,12, the published G, its exact half H, and
1,000 deterministic transcript-derived controls on each curve. No half-generator
entered the predeclared lower 1% tail:

- secp160k1 H lower-tail ranks: 75.2%, 95.6%, 10.8%, 82.5%;
- secp192k1 H: 24.4%, 61.7%, 64.7%, 27.0%;
- secp224k1 H: 45.0%, 31.4%, 28.3%, 84.9%;
- secp256k1 H: 89.6%, 22.8%, 35.3%, 98.9%.

The smallest ranks belonged to published G rather than H: 1.7% for secp192k1 at m=8
and 2.8% for secp256k1 at m=10. Neither crossed the 1% replication trigger, and neither
is significant across the 32 inspected curve/dimension/point endpoints. The 98.9%
secp256k1-H rank is in the opposite direction from the short-relation hypothesis.

Principal files:

- `sage/lll_coordinate_relations.py`
- `scripts/analyze_lll_relations.py`
- `results/lll_sec_discovery_analysis.json`
- `results/lll_secp160k1_discovery.jsonl`
- `results/lll_secp192k1_discovery.jsonl`
- `results/lll_secp224k1_discovery.jsonl`
- `results/lll_secp256k1_discovery.jsonl`

## Fixed-base implementation-leakage proxies

`scripts/fixed_base_leakage.py` evaluates the real G and H points against derived
controls under fixed-window tables of widths 4, 5, and 8. It records standard and
Montgomery coordinate Hamming weights, zero 32/64-bit limbs, pairwise table-entry
distances, and Hamming-weight traces of the high-level intermediates in mixed Jacobian/
affine addition. These are leakage proxies over public values, not measurements from a
CPU or physical device.

The 1,000-control discovery screen found a real representation-level outlier for the
short half-generators. A fresh 10,000-control run on secp224k1 and secp256k1 confirmed:

- secp224k1 H has one completely zero leading x limb in both the tested standard
  32-bit and padded 64-bit layouts; none of 10,000 controls did (smoothed two-sided
  midrank p approximately 1e-4).
- secp256k1 H has two zero 32-bit x limbs or one zero 64-bit x limb in standard form;
  none of 10,000 controls did (p approximately 1e-4).
- secp256k1 H has combined standard x/y Hamming weight 213, below every control
  entry-1 observation (p approximately 1e-4). As the minimum across a width-4 table,
  six controls tied or beat 213 (p=0.00290), reflecting the larger comparison set.
- Montgomery conversion removes the secp224k1 zero-limb artifact. For secp256k1 the
  entry-1 Hamming weight remains low: 217, with two controls tied and only a few below
  it (p=0.000900). This persistence is compatible with the unusually small Montgomery
  radix residue for the pseudo-Mersenne secp256k1 prime.
- The published G points were not outliers. On the two 10,000-control replications the
  smallest published-G proxy p-value was 0.0691.
- The mixed-addition trace proxies did not carry the H encoding anomaly forward. The
  smallest H trace p-value was 0.0983.

This is a genuine but limited implementation observation. If a protocol actually used
H as a fixed base and a physical implementation leaked operand Hamming weights, its
digit-1 table entry could have a more distinctive template. Fixed-base table contents
are public, however, and every digit has a stable public template; this experiment does
not demonstrate secret recovery, timing leakage, or increased ECDLP power. Ordinary
SEC implementations use published G, where the anomaly is absent. The historical
doubling therefore washes out the obvious representation artifact, whatever its reason.

Principal files:

- `scripts/fixed_base_leakage.py`
- `scripts/analyze_fixed_base_leakage.py`
- `results/fixed_base_leakage_discovery_analysis.json`
- `results/fixed_base_leakage_replication_10k_analysis.json`
- `results/fixed_base_leakage_secp224k1_replication_10k.jsonl`
- `results/fixed_base_leakage_secp256k1_replication_10k.jsonl`
