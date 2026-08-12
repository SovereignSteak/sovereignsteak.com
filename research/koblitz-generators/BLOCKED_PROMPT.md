You are a research agent specializing in elliptic-curve cryptanalysis and computational algebraic geometry. Your task is to design, implement, and run a systematic computational experiment investigating the anomalous half-generators of the SECG prime-field Koblitz curves (secp160k1, secp192k1, secp224k1, secp256k1). The goal is NOT to break 256-bit ECDLP; it is to search for structural anomalies that might make the special generator construction interact non-trivially with future non-generic ECDLP techniques (index-calculus / summation-polynomial / Gröbner / small-root / arithmetic-dynamics methods).

Resource constraint: only CPU time is available. Prefer exact arithmetic, symbolic methods, and classical algorithms (Pollard rho, baby-step giant-step, division polynomials, Gröbner bases via Singular or Magma if present, SageMath’s EllipticCurve and NumberField machinery, PARI/GP, sympy). Avoid any deep-learning or GPU-heavy pipelines.

### Background facts you must use (verify them yourself)

The published generators G of the four curves satisfy G = 2H for a point H whose x-coordinate is anomalously short and shares a common 152-bit hex string:

- common core = 8ce563f89a0ed9414f5aa28ad0d96d6795f9c6
- secp160k1 Hx ≈ 0x48ce563f89a0ed9414f5aa28ad0d96d6795f9c62
- secp192k1 Hx ≈ 0x554123b78ce563f89a0ed9414f5aa28ad0d96d6795f9c66
- secp224k1 Hx = 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63
- secp256k1 Hx = 0x3b78ce563f89a0ed9414f5aa28ad0d96d6795f9c63   (only 166 bits)

All four curves are of the form y² = x³ + b over a generalized-Mersenne prime, with CM discriminant −3 (efficient GLV endomorphism). SEC 2 explicitly states that the Koblitz parameters were chosen for the endomorphism and does not claim verifiable randomness for the generators.

It is already known that knowledge of H alone gives a trivial reduction between DLP_G and DLP_H; the doubling does not hide an easier discrete log. The interesting open question is whether the special algebraic form of H (low bit-length + shared core + relation to the GLV orbit) can interact with more sophisticated algebraic attacks.

### Concrete experimental program (execute in order)

1. **Parameter acquisition and verification**
   - Load the exact SEC 2 parameters for the four curves (p, a=0, b, G, n, h=1).
   - Compute H = G * inv(2 mod n) and confirm the x-coordinates and the common 152-bit substring.
   - Record the y-coordinates of H as well, and the action of the GLV endomorphism φ on both G and H.

2. **Reverse-engineering candidate generator recipes**
   Hypothesize and test deterministic generation procedures consistent with the observed H values. Plausible candidates from the SHA-1 era include:
   - Hx obtained by taking a short seed / counter, hashing with SHA-1 (or a truncated SHA-1), optionally prefixing a small constant (0x3b, 0x4, 0x55\ldots), then lifting to a point of the correct order and doubling.
   - Systematic search for small-height points that become generators after doubling.
   - Any procedure that re-uses the same 152-bit core across different field sizes.
   Produce a short list of the most plausible candidate recipes (parameterized by seed length, hash function, prefix rules, etc.). Document which recipes reproduce the four known H’s (or come closest).

3. **Generation of analogous small curves (the core experiment)**
   Using each candidate recipe, generate a large corpus of “suspicious” instances:
   - Field sizes 30–80 bits (plenty of CPU room for exhaustive algebraic attack).
   - Curves of Koblitz type: a=0, b small, p of special form that admits an efficient endomorphism of order 3 or 6 (CM disc −3 or −27, etc.), prime order n ≈ p, cofactor 1.
   - For each such curve produce two bases:
     A. “Special” base Gs obtained by applying the candidate recipe (then doubling if the recipe produces an H).
     B. Uniformly random base Gr of the same order (control).
   Aim for several thousand curves / base pairs. Keep all data (p, b, n, Gs, Gr, Hx, etc.) in a machine-readable table.

4. **Comparative algebraic cryptanalysis**
   For every (curve, Gs) vs (curve, Gr) pair run the following battery of tests and record quantitative differences:

   a. Division polynomials Ψ_k. Look for unexpectedly low-degree factors, sparse polynomials, or factors of unusually low height when the base is Gs.
   b. Summation-polynomial / index-calculus style systems (even if only for very small bit sizes). Compare Gröbner-basis running times, degree of regularity, or number of solutions for the special vs random bases.
   c. Low-height / sparse modular relations. Search the orbit {k·H, φ^i(k·H)} for points whose coordinates (or differences) have unusually small height or sparse binary representation.
   d. GLV-orbit correlations. Measure whether the special generator produces shorter relations inside the GLV lattice or lower-degree invariants under the endomorphism.
   e. Scaling behaviour. Plot attack cost (or algebraic complexity measures) versus bit size for the two families; look for any systematic offset or different asymptotic slope that appears only for the special generators.
   f. Cross-curve relations. Because the four original H’s share a long common substring, test whether analogous shared cores appear across different small fields generated by the same recipe, and whether that produces detectable cross-curve isogenies or common factors in resultants.

5. **Statistical and structural analysis**
   - Produce summary statistics, histograms of heights, degree sequences, Gröbner timings, etc.
   - Flag any outlier families where the special generator is measurably “easier” (or produces qualitatively different algebraic structure) than the random control.
   - If an anomaly appears, try to isolate the minimal mathematical feature responsible (the short Hx, the shared core, the doubling, the GLV interaction, \ldots).

6. **Negative results are valuable**
   Explicitly report when the special construction produces no detectable difference. That still constrains the space of possible hidden representations.

### Deliverables

- Reproducible SageMath / Python / PARI scripts that generate the curve corpus and run the tests.
- A machine-readable dataset of all generated curves and measured invariants.
- A written report that:
  - lists the candidate generator recipes that best explain the original four H’s,
  - quantifies any systematic differences (or the lack thereof) between special and random bases,
  - discusses whether any observed anomaly could plausibly scale or be amplified by a future non-generic ECDLP algorithm,
  - ends with concrete suggestions for the next bit-size range or algebraic technique to try.

Start by verifying the four half-generators, then move to reverse-engineering the most plausible generation recipes, then build the small-curve corpus. Work incrementally; after each major stage write a short status note and the current best hypotheses before continuing. Use only CPU-friendly exact methods.
