# Final report: SECG Koblitz generator-selection study

## Conclusion

The published SECG Koblitz generators have weak and opaque provenance. Their exact
half-generators reuse a conspicuous 152-bit hexadecimal core, and secp224k1 and
secp256k1 use the same integer half-generator x-coordinate. This is a genuine NUMS and
public-confidence problem.

No experiment in this study found credible evidence that the historical construction
changes ECDLP difficulty under the nongeneric mechanisms tested or creates a
base-specific algebraic shortcut. Historical-style, uniformly sampled, and
transcript-derived NUMS bases behaved alike under those experiments.

This is evidence against effects represented by the tested models, not a universal
proof against all future nongeneric algorithms.

Shoup's [generic-group lower bounds](https://link.springer.com/chapter/10.1007/3-540-69053-0_18)
explain why changing a nonidentity generator cannot improve an abstract generic attack.
Coordinates, encodings, endomorphisms, implementation
behavior, and relations between multiple protocol generators are outside that model and
must be considered separately. In particular, a known relation `H=[a]G` can invalidate
the binding or independence assumptions of multi-generator protocols even when
single-base ECDLP is unchanged.

## Prior work and novelty

The half-generator anomaly was not first observed here. Heninger, Scholl, and Shumow
presented the exact secp160k1 half-coordinate in a Crypto 2019 rump-session talk, and
DiSSECT (ePrint 2022/943) subsequently used `x([k^-1]G)` for `k=1,...,8` as a curve
trait, identifying secp224k1 and secp256k1 as exceptional among comparable standards.

This project's contribution is the exact reconstruction across all four prime-field
k1 curves; controlled analogue corpora; blinded Semaev/Gröbner experiments; replicated
GLV scans; real-curve coordinate-relation and implementation-proxy tests; direct
reproduction of the inverse-scalar distinguisher; and a sourced investigation of the
historical doubling convention.

## Historical reconstruction

Exact SEC 2 verification established `H = [inverse(2) mod n]G` and `2H=G` for all four
curves. Every `x(H)` contains:

`8ce563f89a0ed9414f5aa28ad0d96d6795f9c6`

The best descriptive reconstruction is a fixed hexadecimal core with short affixes,
followed by point lifting and doubling. Simple ascending “first liftable affix” scans do
not reproduce the observed values. A bounded SHA-1 label/counter search found no match,
but unknown seeds and serializations prevent a historical proof.

Generic SHA-1 rainbow tables are not recommended. They normally target known password
formats and full digests; here the input domain, serialization, truncation, affix rule,
and acceptance conditions are unknown. A table miss would carry almost no evidentiary
weight. Only a historically justified dictionary and message format would make a new
SHA-1 search worthwhile.

## Experimental evidence

The primary corpus contains 2,000 exact prime-order, cofactor-one, j=0 curves from 30 to
80 bits. A later high-power corpus contains 1,000 curves from 30 to 36 bits with one
historical-style base, one full-x NUMS base, and 16 independent uniform controls per
curve.

Initial orbit tests found no historical/control differences in coordinate length,
sparsity, minimum centered coordinate, or scaling. Division-polynomial factors and the
GLV scalar lattice were confirmed to be curve-level rather than base-level properties.

The exact DiSSECT inverse-scalar trait was then reproduced on the real curves against
2,000 controls each. For secp224k1 and secp256k1, `k=2` exposes a 166-bit x-coordinate;
the shortest control coordinates were respectively 212 and 242 bits (two-sided
empirical midrank p=0.000500 for each). secp160k1 and secp192k1 were ordinary under the
same aggregate metrics. Broader exploratory scalar families found no new witness:
`k=2` remained responsible for every 224/256 distinction. This is a strong public
parameter distinguisher but supplies no small ECDLP secret.

Two-summand Semaev tests gave:

| factor-base size | historical | random | paired incidence p | capped timing p |
|---:|---:|---:|---:|---:|
| 48 | 53/200 | 53/200 | 1.000 | 0.887 |
| 64 | 66/200 | 70/200 | 0.627 | 0.688 |

Three-summand Semaev f4 tests on the original eight-control high-power design gave:

| factor-base size | historical success | control mean | difference | 95% interval | exchangeability p |
|---:|---:|---:|---:|---:|---:|
| 12 | 28.50% | 27.21% | +1.29 points | -1.09 to +3.69 | 0.309 |
| 16 | 43.70% | 44.06% | -0.36 points | -2.75 to +2.05 | 0.783 |
| 24 | 66.90% | 66.15% | +0.75 points | -1.51 to +3.00 | 0.526 |
| 32 | 82.00% | 81.34% | +0.66 points | -1.25 to +2.58 | 0.543 |

The joint grid-wide success comparison was 55.28% historical versus 54.69% control,
with p=0.466 and a 95% interval of -0.95 to +2.12 percentage points. Historical mean
rank was 5.02 among nine bases, versus the null expectation 5.00.

That interval is also a precision statement: within this experimental design, the data
are inconsistent at the 95% level with a historical-base incidence advantage larger
than about 2.1 percentage points. It does not bound effects in untested attack models.

The grid-wide capped first-relation statistic had p=0.087. This small, nonsignificant
direction was investigated with eight fresh controls. The completed 16-control
replications were:

| factor-base size | historical | 16-control mean | incidence p | timing p | historical rank / null |
|---:|---:|---:|---:|---:|---:|
| 12 | 28.50% | 26.81% | 0.163 | 0.082 | 8.85 / 9.00 |
| 16 | 43.70% | 43.69% | 1.000 | 0.107 | 8.84 / 9.00 |
| 24 | 66.90% | 66.76% | 0.925 | 0.365 | 8.85 / 9.00 |

The weak timing direction did not translate into abnormal incidence or rank and was not
strengthened consistently as relation density changed. NUMS bases sometimes showed the
same direction. It is best interpreted as ordinary sampling variation, not a historical
generator effect. The adaptive size-32 extension was not needed to reach this conclusion;
the original size-32 experiment was already complete and null.

SageMath independently validated every SEC calculation, all 2,000 primary-corpus group
orders, all checked base orders, 352 two-summand witnesses, and all 52 three-summand
witnesses without failure. Singular verified representative non-unit f3 and f4 ideals.
The resultant-defined j=0 f4 polynomial has total degree 12 and 125 terms. Some f4
Groebner computations have heavy-tailed runtimes, but no completed result associates
that behavior with a base class.

## Recommendation

For protocols requiring independent generators, derive each point directly from a
public transcript using a versioned, domain-separated hash-to-curve procedure:

1. Commit to protocol, curve, roles, encoding, and generator count before selecting the
   public seed.
2. Obtain the seed from a future randomness beacon or multi-party commit/reveal.
3. Where a reviewed suite exists, use the standardized hash-to-curve construction—for
   example, RFC 9380 defines suites for secp256k1. Do not hash to a scalar and multiply
   the existing generator, because that publishes the discrete-log relation.
4. For a one-time ceremony on a curve without a standardized suite, an explicitly
   specified SHAKE256 candidate-x rejection procedure remains auditable, but should be
   described as a project-specific map rather than a general hash-to-curve standard.
5. Publish the complete transcript, suite or map identifier, and resulting point.
6. Verify canonical encoding, on-curve status, nonidentity, correct subgroup order,
   distinctness up to sign, and distinctness across the GLV orbit.
7. Do not derive one protocol generator as a publicly or privately known scalar multiple
   of another.

This construction preserves GLV acceleration; the endomorphism and its scalar lattice
do not depend on which nonzero generator is named.

## Reproducibility and principal files

- `scripts/verify_sec2.py`: published parameters, halves, and GLV verification.
- `scripts/reverse_engineer.py`: bounded recipe tests.
- `scripts/generate_corpus.py`: primary curve corpus.
- `scripts/expanded_relations.py`: exact two- and three-summand witness scanner.
- `sage/further_analysis.py`: Sage order and division-polynomial checks.
- `sage/verify_relations.py` and `sage/verify_f4.py`: independent witnesses and ideals.
- `scripts/derive_sec2_generators.py`: recommended generator derivation.
- `scripts/inverse_scalar_traits.py`: DiSSECT-trait reproduction and extensions.
- `results/inverse_scalar_traits_analysis.json`: inverse-orbit empirical ranks.
- `results/high_value_grid_analysis.json`: joint preregistered result.
- `results/high_value_16c_b12_analysis.json`, `high_value_16c_b16_analysis.json`, and
  `high_value_16c_b24_analysis.json`: adaptive fresh-control checks.

Primary corpus SHA-256:

`a12f607eb7465417056417ad2048906690a4c197e0d8d4787a051baa5706c052`

High-power corpus SHA-256:

`896fd94f509e1961d0592c33442654c55120950df4cdfbbbea0da513ba6cf474`

## Bottom line

The historical generator-selection process should not be copied because it is opaque
and creates avoidable suspicion. The measured algebraic behavior supports a narrower
statement: no tested nongeneric mechanism made these generators easier for ECDLP. The
observed coordinate artifact is a strong provenance distinguisher, but no tested result
turns it into a cryptographic trapdoor.
