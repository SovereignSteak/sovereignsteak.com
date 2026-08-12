# SECG Koblitz generator provenance and higher-assurance alternatives

## Result in brief

The four half-generators are verified exactly. Their shared 152-bit substring is real,
and the 224- and 256-bit curves use exactly the same integer `x(H)`. A fixed hexadecimal
core with short affixes, followed by lift and doubling, is therefore the best descriptive
recipe. The historical selection rule and intent remain unknowable from public points.

Across 2,000 analogous 30–80-bit prime-order `j=0` curves, the fixed-core construction
showed no detectable difference from exact-rejection uniform controls in the measured
short scalar/GLV orbits. This is a negative result, not a security proof.

## Exact historical verification

`scripts/verify_sec2.py` checks curve membership, `nG=O`, computes
`H=[2^-1 mod n]G`, checks `2H=G`, and derives compatible cube roots `beta` and `lambda`
such that `phi(x,y)=(beta*x,y)=[lambda](x,y)` for both G and H. Full values are stored
in `results/sec2_verification.json`.

The half-generator x decompositions are:

| curve | prefix | shared 152-bit core | suffix |
|---|---:|---|---:|
| secp160k1 | `4` | `8ce563f89a0ed9414f5aa28ad0d96d6795f9c6` | `2` |
| secp192k1 | `554123b7` | same | `6` |
| secp224k1 | `3b7` | same | `3` |
| secp256k1 | `3b7` | same | `3` |

## Ranked reconstruction

1. Fixed 152-bit hexadecimal core, short curve-specific affix, lift, double. Exact
   descriptive fit; the affix search rule is unknown.
2. Reuse a low-height candidate across field sizes and scan nearby values until lift
   and group tests pass. It explains the 224/256 equality but many scan orders fit.
3. Short seed/counter through SHA-1, truncate/affix, lift, double. A declared search of
   nine labels, 100,000 counters, and three encodings found no hit. This does not exclude
   an unknown seed or serialization.

## Corpus construction and findings

For `p=u^2+3v^2`, the six CM traces were enumerated; prime `p`, prime `n=p+1-t`, and a
small `b` whose curve has that order were retained. Thus every row is a cofactor-one
`y^2=x^3+b` curve with the cube-root GLV map. Each nonzero point is a generator.

The corpus is `data/corpus.jsonl` (2,000 rows, SHA-256
`a12f607eb7465417056417ad2048906690a4c197e0d8d4787a051baa5706c052`). Historical
and random paired differences gave randomization p-values 0.787 for x bit length,
0.179 for minimum orbit popcount, and 0.985 for log2 minimum centered orbit x. The
scaling slopes for that last measure were 1.003 (historical), 0.998 (random), and
1.000 (NUMS). No tested signal distinguishes the historical-style base.

The full-length NUMS base predictably has a longer initial x (p<1e-4); its orbit metrics
do not differ from random. Full-length rejection is therefore cosmetic/provenance
hardening, not evidence of cryptographic hardness.

Two proposed measures require careful interpretation. Division polynomials depend on
the curve, not on which generator is named, so within-curve base comparisons are
identical. Likewise the GLV lattice depends on `(n,lambda)`, not the nonzero base. A
base may change constants in a summation-polynomial system. The initial pass had no CAS;
the later Sage/Singular follow-up below supplies a bounded toy Gröbner experiment.

## Ready-to-use recommendation

Use `scripts/derive_sec2_generators.py` with these rules:

1. Commit publicly to the curve, protocol, roles, generator count, encoding, and scheme
   version before selecting a seed. Take the seed from a future public randomness beacon
   or a multi-party commit/reveal transcript.
2. Domain-separate protocol, curve parameters, role/index, seed, and version. SHAKE256
   produces candidate x and sign bits; reject x>=p, non-residues, infinity, wrong order,
   and (optionally) non-full-length x. Publish the transcript, counter, and point.
3. Derive every role under a distinct label/index. Do not create `H=[known scalar]G`:
   whoever selected that scalar would know the discrete-log relation. Direct hash-to-point
   derivation avoids constructing such a known relation.
4. Verify on-curve, nonidentity, `[n]P=O`, distinctness up to sign and GLV orbit, and the
   canonical encoding in at least two independent implementations. Cofactor-clear on
   curves with h>1; these four have h=1.
5. Keep GLV acceleration: generator choice does not alter the endomorphism or its scalar
   lattice. Treat full-length x as removal of a visual artifact, not a hardness claim.

Example:

```bash
python3 scripts/derive_sec2_generators.py \
  --protocol example-v1 --role commitment-base \
  --seed 'PUBLIC-BEACON-VALUE-AFTER-COMMITMENT' --count 3
```

## Limits and next experiments

The 2,000 curves are CM-constructed experimental analogues, not independent random
curves; the orbit scan stops at k=32; and absence of a detected signal is not an ECDLP
reduction. Next, use the now-available Sage plus Singular and pre-register: 81–128-bit
curves, fixed summation-polynomial systems and monomial orders, wall/CPU time and degree-of-regularity
endpoints, blinded base labels, and survival analysis for timeouts. Extend low-height
searches with LLL on explicitly defined coordinate embeddings and increase k geometrically.
Cross-check selected 30–45-bit instances using Pollard rho to confirm the expected
sqrt(n) scaling while recognizing that generic rho is mathematically base-invariant.

## SageMath follow-up

SageMath 10.9 subsequently became available. `sage/further_analysis.py` independently
recomputed the orders of all four SEC curves, their generator orders and halves, and
all 2,000 corpus curve orders and three base orders. There were zero failures.

Sage factored division polynomials `psi_3` through `psi_12` on 120 corpus curves (1,200
curve/polynomial records). Low-degree factors occur frequently—for example all 120
`psi_3`, `psi_6`, `psi_9`, and `psi_12` records have a factor of degree at most two.
This follows the visible `j=0`/order-three structure (for example `psi_3` always has an
`x` factor here), and is exactly identical for all three bases on a curve. It is not a
historical-generator anomaly.

For an index-calculus-style toy test, the experiment used the exact Semaev system
`<f3(x1,x2,xQ), product(x1-B), product(x2-B)>` over `GF(p)` with 48 liftable x values.
For each base it scanned multiples until a decomposable target was witnessed, capped at
300,000, then invoked Singular's lexicographic Gröbner basis through Sage. On 12 matched
30–40-bit curves, relations were found for 4 historical, 3 random, and 3 full-x NUMS
bases. Found-relation medians were respectively 42,165.5, 123,452, and 40,119, but 8–9
of 12 observations per group were censored. An exact paired sign-flip test on capped
values gives p=0.125 for historical versus random and p=1.0 for NUMS versus random.
This small, heavily censored sample provides no statistically established difference.
All solved Gröbner bases had maximum degree 2 and millisecond-scale solve times; orbit
relation search, not Gröbner reduction, dominated CPU time.

Machine-readable Sage results are in `results/sage_analysis.json` and the compact,
censor-aware summary is in `results/sage_summary.json`. A stronger follow-up should use
a compiled orbit scanner, at least several hundred matched curves, multiple factor-base
sizes, and a pre-specified survival-analysis model.

## Expanded witnessed-relation study

`scripts/analyze_affixes.py` first tested the simplest counter explanation for the SEC
coordinates. Holding each published prefix and the common core fixed, the observed
suffix has lift rank 2, 2, 1, and 1 (zero-based) for 160, 192, 224, and 256 bits. It is
never the first liftable suffix. Nor is any observed prefix the first lift in its tested
ascending window. This weakens simple “increment the visible affix from zero” recipes,
although it cannot exclude an unknown ordering or additional acceptance condition.

The relation experiment was then expanded with `scripts/expanded_relations.py`. It uses
mixed Jacobian additions and batch inversion, cross-checked against the affine reference,
to scan 200 matched 30–40-bit curves. For each base it used 48 liftable factor-base x
values and searched through 500,000 multiples for the first target decomposable through
Semaev `f3`. This produced 600 right-censored records:

| comparison | left successes | random successes | left-only | random-only | McNemar p | capped paired p |
|---|---:|---:|---:|---:|---:|---:|
| historical vs random | 53 | 53 | 19 | 19 | 1.000 | 0.887 |
| full-x NUMS vs random | 46 | 53 | 16 | 23 | 0.337 | 0.100 |

Success frequency falls sharply with field size, as expected at fixed factor-base size
and search bound, but every comparison is paired within the same curve. There is no
evidence that historical-style bases reach a two-factor-base relation earlier or more
often than uniform controls. The equality of both historical/random success and
discordant counts is a particularly direct negative result.

Sage independently checked all 152 successful witnesses: `x([k]P)` matched the recorded
target and Semaev `f3` had factor-base solutions in every case. Singular then verified
60 selected ideals; none was the unit ideal, every basis had two elements, 59 had maximum
degree 2 and one degree 1. Machine-readable files are `results/relations.jsonl`,
`results/relations_analysis.json`, `results/relations_sage_verification.json`, and
`results/affix_analysis.json`.

The next step is no longer merely a larger scan. It should vary factor-base size on the
same curves, pre-register a discrete-time survival or conditional hazard model, and test
three- and four-summand Semaev systems where degree of regularity becomes nontrivial.

As an immediate replication, the identical 200 curves and 500,000-multiple bound were
rerun with 64 rather than 48 factor-base x values. Relation counts rose, as expected:
historical 66/200, random 70/200, and NUMS 64/200. Historical versus random gave
McNemar p=0.627 and capped paired p=0.688; NUMS versus random gave p=0.441 and p=0.152.
The null conclusion is therefore stable across both tested factor-base sizes. Sage
verified all 200 successful size-64 witnesses plus 30 Singular bases with zero failures.
The replication data are `results/relations64.jsonl`, `results/relations64_analysis.json`,
and `results/relations64_sage_verification.json`.

## Three-summand Semaev f4 experiment

The scanner was generalized from pair sums to signed triple sums, testing a genuinely
different algebraic relation rather than only increasing the earlier sample. On 100
matched 30–40-bit curves, with 12 liftable factor-base x values and the same 500,000
bound, the results were:

| comparison | left successes | random successes | left-only | random-only | McNemar p | capped paired p |
|---|---:|---:|---:|---:|---:|---:|
| historical vs random | 17 | 14 | 8 | 5 | 0.581 | 0.337 |
| full-x NUMS vs random | 21 | 14 | 11 | 4 | 0.118 | 0.165 |

Neither comparison is statistically significant. Most successes occur at 30–33 bits;
larger rows are heavily right-censored, so medians of successful observations alone must
not be interpreted as comparative performance.

`sage/verify_f4.py` constructs Semaev f4 as
`Res_z(f3(x1,x2,z), f3(x3,xQ,z))`. Because Sage does not directly implement the needed
multivariate resultant over primes above 2^29, the script computes one universal exact
template over ZZ and reduces it modulo each p. The resulting j=0 polynomial has total
degree 12 and 125 terms. Sage independently verified all 52 scalar/triple witnesses with
zero failures. Three full factor-base-12 ideals and three smoke factor-base-10 ideals
were solved by Singular: all were non-unit, with maximum Gröbner degree 2–3 and
millisecond CPU times.

Attempts to extend the Gröbner sample exposed a severe heavy tail in some f4 systems;
Singular's in-process C call does not reliably honor Python alarm timeouts. This is an
engineering limitation, not evidence for either base class. A sound larger timing study
should execute one ideal per external process under an OS-enforced timeout, randomize or
blind base labels, and analyze timeouts as right-censored outcomes.

The machine-readable outputs are `results/relations_f4.jsonl`,
`results/relations_f4_analysis.json`, `results/relations_f4_sage.json`, and
`results/relations_f4_sage_three.json`.
