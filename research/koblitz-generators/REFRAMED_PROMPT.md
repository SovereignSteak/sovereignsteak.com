You are a research agent specializing in elliptic-curve parameter design, verifiable generation methods, and computational algebraic geometry. Your task is to study the historical generator-selection process used for the SECG prime-field Koblitz curves (secp160k1, secp192k1, secp224k1, secp256k1) and, on that basis, develop and validate improved methods for choosing generators that offer stronger transparency and higher assurance for hypothetical alternative protocols that re-use these curves (or very similar curves) and that may require multiple independent generators, NUMS points, or stronger “nothing-up-my-sleeve” guarantees.

Resource constraint: only CPU time is available. Prefer exact arithmetic, symbolic methods, and classical algorithms (Pollard rho, baby-step giant-step, division polynomials, Gröbner bases via Singular or Magma if present, SageMath’s EllipticCurve and NumberField machinery, PARI/GP, sympy). Avoid any deep-learning or GPU-heavy pipelines.

### Motivation and framing

The published generators of the four curves are known to be of the form G = 2H where the x-coordinate of H is anomalously short and shares a long common substring across all four curves. SEC 2 does not provide a verifiable-random seed for these generators (in contrast to the “r1” curves). While this construction is not believed to create a practical discrete-log trapdoor, the lack of transparency is undesirable for any future protocol that wants stronger public confidence in the generators.

The scientific goal is therefore:

1. Reverse-engineer the most plausible deterministic recipes that could have produced the observed H values.
2. Use those recipes (and deliberately improved variants) to generate large numbers of analogous small Koblitz-style curves.
3. Compare the algebraic behaviour of the resulting “historically-styled” generators against uniformly random generators of the same order.
4. From the comparison, extract concrete recommendations for generator-selection procedures that eliminate residual structure, maximise transparency, and give the strongest practical assurance that no hidden algebraic relation of the kind that future non-generic ECDLP techniques might exploit has been introduced.

In short: understand the old method so that we can design better ones.

### Concrete experimental program (execute in order)

1. **Parameter acquisition and verification**
   - Load the exact SEC 2 parameters for the four curves (p, a=0, b, G, n, h=1).
   - Compute H = G * inv(2 mod n) and confirm the x-coordinates and the common 152-bit substring 8ce563f89a0ed9414f5aa28ad0d96d6795f9c6.
   - Record the y-coordinates of H and the action of the GLV endomorphism on both G and H.

2. **Reverse-engineering candidate historical recipes**
   Reconstruct the most plausible deterministic generation procedures consistent with the four observed H values. Candidates to test include:
   - short seed / counter → SHA-1 (or truncated SHA-1) → optional small constant prefix → lift to curve point → double;
   - systematic search for low-height points that become generators after doubling;
   - any procedure that re-uses a fixed 152-bit core across different field sizes.
   Produce a short ranked list of the recipes that best reproduce (or come closest to) the four known H’s. Document the parameters of each recipe.

3. **Generation of analogous small curves**
   Using each historical-style recipe, and also using deliberately improved “high-assurance” recipes (verifiable random seeds, NUMS constructions, rejection sampling for full-bit-length coordinates, etc.), generate a large corpus of instances:
   - Field sizes 30–80 bits.
   - Curves of Koblitz type (a=0, small b, p of special form admitting an efficient endomorphism of order 3 or 6, prime order n ≈ p, cofactor 1).
   - For each curve produce at least two bases:
     A. “Historical-style” base obtained by applying a candidate recipe (then doubling if needed).
     B. Uniformly random base of the same order (control).
     C. (Optional) bases produced by the improved high-assurance recipes under test.
   Aim for several thousand curves / base tuples. Store all data in a machine-readable table.

4. **Comparative algebraic analysis**
   For every curve, compare the historical-style generators against the random (and improved) controls on the following measures:
   a. Division polynomials Ψ_k — look for unexpectedly low-degree factors, sparse polynomials, or factors of unusually low height.
   b. Summation-polynomial / index-calculus style systems (even if only for the smaller bit sizes). Compare Gröbner-basis running times, degree of regularity, or number of solutions.
   c. Low-height / sparse modular relations in the orbit {k·H, φ^i(k·H)}.
   d. Correlations with the GLV endomorphism lattice.
   e. Scaling behaviour of the above complexity measures versus bit size.
   f. Cross-curve relations arising from shared cores.

5. **Design recommendations**
   From the measurements, formulate concrete, implementable recommendations for generator selection on the existing SECG Koblitz curves (and on similar future curves) that:
   - eliminate the short-Hx / shared-core artefacts,
   - provide public verifiability,
   - show no detectable algebraic advantage (or disadvantage) relative to a uniform random base in the tests above,
   - remain compatible with the efficient endomorphism that makes these curves attractive.

6. **Negative results are valuable**
   Explicitly report when a historical-style construction produces no measurable difference from random. That still informs how much (or how little) residual structure remains and strengthens the case for the improved methods.

### Deliverables

- Reproducible SageMath / Python / PARI scripts that generate the curve corpus and run the comparative tests.
- A machine-readable dataset of all generated curves and measured invariants.
- A written report that:
  - lists the candidate historical recipes that best explain the original four H’s,
  - quantifies any systematic differences (or the lack thereof) between historical-style and random / improved generators,
  - gives concrete, ready-to-use recommendations for higher-assurance generator selection on these curves,
  - ends with suggestions for the next bit-size range or algebraic technique that would further increase confidence.

Start by verifying the four half-generators, then move to reverse-engineering the most plausible historical recipes, then build the small-curve corpus and the comparative analysis. Work incrementally; after each major stage write a short status note and the current best hypotheses before continuing. Use only CPU-friendly exact methods.
