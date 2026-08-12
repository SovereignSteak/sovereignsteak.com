# Incremental status and hypotheses

## Stage 1 — SEC 2 verification (complete)

All four published points lie on their stated curves and satisfy `n*G = O`. Exact
halving by `inverse(2) mod n` gives `2H=G`. Every `Hx` contains the same 152-bit
hexadecimal core. The complete coordinates and the compatible GLV `(beta, lambda)`
orientation are in `results/sec2_verification.json`.

Current hypothesis: the literal reuse is real, not a display coincidence. In
particular, secp224k1 and secp256k1 use the same integer `Hx`.

## Stage 2 — recipe reconstruction (complete, historically underdetermined)

The fixed-core/short-affix/lift/double family fits all four exactly. A nearby
low-height scan is plausible but its scan order cannot be inferred. A bounded SHA-1
label/counter search found no match; unknown seeds and encodings remain untestable.

Current hypothesis: literal hexadecimal templating or reuse is better supported than
four independent hash outputs. No claim about the designers' intent is justified.

## Stage 3 — analogous corpus (complete)

The dataset contains 2,000 prime-order, cofactor-one, `j=0` curves from 30 through 80
bits. Each has a fixed-core scan/double base, an exact-rejection uniform control, and
a transcript-derived full-length-x NUMS base. Exact order tests passed for every base.

## Stage 4 — comparative analysis (complete within available toolchain)

The `k<=32` scalar orbit and all three GLV images show no significant historical/control
difference. Division polynomials and the GLV lattice are base-independent, an important
correction to the proposed comparison. The initial environment had no usable CAS, so no
timings were invented; a later Sage 10.9 follow-up now provides a bounded Semaev/Singular
experiment in `results/sage_analysis.json`.

## Stage 5 — Sage follow-up (complete, exploratory)

Sage independently validated all 2,000 corpus orders and all published SEC calculations
with zero failures. It factored division polynomials through `psi_12` on 120 curves and
confirmed that common low-degree factors are `j=0` curve structure, identical for every
base. Twelve matched, heavily censored Semaev factor-base trials found no significant
historical/control difference (exact capped paired p=0.125).

## Stage 6 — expanded relation and affix analysis (complete)

Natural ascending affix scans do not reproduce the published points as first successful
lifts. A batch-normalized projective scanner expanded the Semaev relation experiment to
200 matched curves and 600 bases. Historical and random bases each had 53 successes;
both paired tests are decisively null (McNemar p=1.0, capped sign-flip p=0.887). Sage
verified all 152 successful scalar/Semaev witnesses and 60 Singular Gröbner bases with
zero failures.

A factor-base-size-64 replication on the same 200 curves also remains null: historical
66/200 versus random 70/200 relations, McNemar p=0.627 and capped paired p=0.688. Sage
verified all 200 successful witnesses and 30 additional Gröbner bases without failure.

## Final high-power study (complete)

One thousand 30–36-bit curves with eight controls each were tested across f4 factor-base
sizes 12, 16, 24, and 32. All individual and joint incidence comparisons were null; the
joint historical/control p-value was 0.466 and mean rank was 5.02 versus null 5.00. A
small nonsignificant capped-timing direction (p=0.087) prompted an adaptive set of eight
fresh controls. Completed 16-control replications at sizes 12, 16, and 24 remained null,
including incidence p-values 0.163, 1.000, and 0.925. The investigation is wrapped up in
`FINAL_REPORT.md`.

## Stage 7 — three-summand Semaev f4 study (complete, exploratory)

On 100 matched curves with 12 factor-base x values and a 500,000-multiple bound,
historical/random/NUMS bases produced 17/14/21 three-summand relations. Historical
versus random remains nonsignificant (McNemar p=0.581; capped paired p=0.337). Sage
verified all 52 witnesses. The exact resultant-defined f4 has degree 12 and 125 terms;
six tractable Singular systems were non-unit with maximum basis degree 2–3. Some later
systems show severe Gröbner heavy tails, but no completed observation ties this to base type.

Current hypothesis: the visible coordinate structure harms provenance, but the tested
algebraic observables provide no evidence of a base-specific ECDLP shortcut.
