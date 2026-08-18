# Inverse-scalar traits and the DiSSECT distinguisher

## Prior work and purpose

The `G/2` anomaly was public before this project. Heninger, Scholl, and Shumow's
Crypto 2019 rump-session talk was titled
[`48ce563f89a0ed9414f5aa28ad0d96d6795f9c62`](https://www.youtube.com/watch?v=NGLR2N4EK58),
the exact secp160k1 half-generator x-coordinate. DiSSECT later included the values
`x([k^-1]G)`, for `k=1,...,8`, among its traits and found secp224k1 and secp256k1
exceptional among similarly sized standardized curves. See
[DiSSECT, ePrint 2022/943](https://eprint.iacr.org/2022/943) and its
[project paper](https://dissect.crocs.fi.muni.cz/static/dissect.pdf).

The contribution here is not discovery of that distinguisher. This experiment
reproduces it against independently derived controls on all four prime-field SEC k1
curves, identifies the responsible inverse scalar, and extends the same measurements
to several explicitly exploratory scalar families.

## Design

For each published generator `P=G` and nonzero scalar `k`, the experiment computes
`x([k^-1 mod n]P)`. The primary family exactly follows the cited DiSSECT trait:
`k=1,...,8`. Each real generator was compared with 2,000 deterministic
transcript-derived points on the same curve. Recorded aggregate metrics are minimum x
bit length, minimum x Hamming weight, maximum leading-zero bits, and maximum zero 32-
and 64-bit limbs.

Four exploratory families used 250 fresh controls per curve:

- `k=1,...,32`;
- powers of two through 256;
- 8-bit scalars of Hamming weight at most two; and
- deduplicated scalar classes `u+v*lambda` for `u,v` in `[-4,4]`, up to sign.

The implementation uses exact Jacobian arithmetic and batch inversion. All primary
published-generator coordinates were cross-checked against the project's independent
affine reference implementation.

## Primary result

| curve | published minimum x bits | witness k | control range | two-sided empirical midrank p |
|---|---:|---:|---:|---:|
| secp160k1 | 154 | 3 | 147–160 | 0.161 |
| secp192k1 | 187 | 2 | 180–192 | 0.367 |
| secp224k1 | 166 | 2 | 212–224 | 0.000500 |
| secp256k1 | 166 | 2 | 242–256 | 0.000500 |

For secp224k1, `k=2` also produced one zero 32-bit x limb, versus zero for every
control. For secp256k1 it produced two, again versus zero for every control. The
secp256k1 minimum x Hamming weight was 88, below the complete control range 96–130.
The secp224k1 weight of 88 was unusual but not unique after searching eight values
(two-sided empirical p=0.0185).

This precisely reproduces the known mechanism: the inverse orbit reaches the
structured half-point at `k=2`. The corresponding aggregate traits for secp160k1 and
secp192k1 were not exceptional even though their half-points contain the same core.

## Exploratory result and interpretation

Every broader family retained the secp224k1/secp256k1 bit-length and zero-limb
distinction. In every case the witness remained `k=2`. No new structured inverse scalar
was exposed. With 250 controls, the extreme two-sided empirical midrank p-value is
0.00398; these exploratory values are not multiplicity-adjusted.

The result is a reliable curve-parameter distinguisher, not an ECDLP shortcut. Both the
generator and all inverse-orbit coordinates are public, and the short coordinate is not
the unknown discrete-log scalar. It nevertheless matters to provenance: it shows that
the anomaly survives exactly in a previously published coordinate-based trait and is
not merely visible typography.

Principal files:

- `scripts/inverse_scalar_traits.py`
- `scripts/analyze_inverse_scalar_traits.py`
- `results/inverse_scalar_traits_dissect_2k.jsonl`
- `results/inverse_scalar_traits_extended_250.jsonl`
- `results/inverse_scalar_traits_analysis.json`
