# Historical research: why publish G = 2H?

## Finding in brief

No located primary source explains why Certicom published twice the structured source
point for all four prime-field SEC Koblitz curves. The evidence does, however, identify
a plausible benign lineage: Certicom-era point-generation procedures routinely formed a
candidate point U and then published a fixed multiple hU to clear the cofactor. Binary
Koblitz curves of the same era normally had h=2 or h=4. A factor-2 postprocessing step
could therefore have been inherited when the prime-field Koblitz family was assembled.

That explanation is incomplete: secp160k1, secp192k1, secp224k1, and secp256k1 all have
published cofactor 1, so their required cofactor-clearing multiplier is 1, not 2. No
standard located recommends an extra doubling on a prime-order curve.

## Primary-source chronology

1. Certicom's ECC Challenge (1997) specifies SHA-1-based generation of a candidate point
   U followed by `P = hU`, where h is the curve cofactor. It explicitly describes both
   generation and verification of this relation. This predates SEC 2.
   <https://www.certicom.com/content/dam/certicom/images/pdfs/cert_ecc_challenge.pdf>
2. FIPS 186-2 describes binary Koblitz curves with cofactor 2 when a=1 and cofactor 4
   when a=0. This makes multiplication by 2 or 4 routine in the closely related Koblitz
   parameter workflow.
   <https://www.certicom.com/content/dam/certicom/images/pdfs/fips186-2-change1.pdf>
3. SEC 2 version 1.0 (2000) says the prime-field Koblitz curves were obtained by repeatedly
   selecting endomorphism-friendly parameters until a prime-order curve was found. It
   gives no generator-selection seed, recipe, or rationale for doubling.
   <https://www.secg.org/SEC2-Ver-1.0.pdf>
4. SEC 1 version 2 later standardized the same general pattern for verifiably random base
   points: hash to R, then compute `G = hR`. It also makes clear that h is the actual
   cofactor, not an arbitrary whitening multiplier.
   <https://www.secg.org/sec1-v2.pdf>
5. Modern hash-to-curve guidance is explicit that cofactor clearing is multiplication by
   h (or a proven equivalent effective cofactor), and that no operation is needed when
   h=1. This confirms that extra doubling has no standard subgroup-clearing purpose here.
   <https://www.rfc-editor.org/rfc/rfc9380.html>

## Additional evidence from the parameters

- All four recovered H points use the even-y lift. This strongly fits a deterministic
  `x -> canonical lift -> fixed multiplication` recipe.
- The common 152-bit core is close to the SHA-1 output width used throughout contemporary
  Certicom generation procedures. A single 160-bit-era value with curve-specific affixes
  is more plausible than four independent digests.
- secp224k1 and secp256k1 reuse exactly the same x(H), which is consistent with reusing a
  source point template across curves and inconsistent with independent uniform point
  generation.
- Doubling maps the short/template coordinate through a nonlinear rational function and
  normally produces a full-width-looking x(G). The project's implementation experiment
  confirms that the zero-limb/low-weight H encoding anomaly is absent from G.

These facts establish a shared deterministic construction but do not identify its seed,
message format, or motivation.

## Candidate justifications, ranked

### 1. Inherited cofactor-clearing workflow — plausible, best benign explanation

The workflow `candidate U -> fixed small multiple -> published base point` was standard
Certicom practice before SEC 2, and a multiplier of 2 was ubiquitous for binary curves.
Reusing a common parameter-generation tool or convention is credible. The weakness is
that a correct implementation should have used the actual cofactor, which is 1 here.

### 2. SHA-1-width source followed by coordinate whitening — plausible but undocumented

A roughly 160-bit digest or constant can be lifted directly on every curve. Doubling then
makes the published coordinate look field-sized and removes conspicuous leading zero
limbs. This matches the observed data very well. No located contemporary source says
that Certicom used doubling as a randomness extractor or presentation step, and one
doubling does not make the distribution uniform: the output family still contains at
most as many points as the source family.

### 3. Compact multi-curve parameter storage — possible, weak evidence

An implementation could store the shared 152-bit x core, small affixes, and an even-y
rule, reconstruct H, and double to obtain each standardized G. This could reduce ROM in
an embedded multi-curve product. Against it, square-root recovery plus doubling costs
more code and computation, and deployed implementations normally store G or a much
larger fixed-base precomputation table. No product documentation supporting this design
was located.

### 4. Avoid visibly low-weight operands or implementation leakage — technically real,
but historically unsupported

This project confirmed that H is an extreme standard-encoding outlier while G is normal.
Publishing G avoids zero-limb and low-Hamming-weight base-table entries. There is no
evidence that this was the designers' motivation, and public table entries already have
known templates. Treat this as a consequence, not an established rationale.

## Explanations that do not fit

- **Required subgroup clearing:** h=1, so standards require no multiplication.
- **GLV acceleration:** the endomorphism and scalar lattice depend on the curve and n,
  not on replacing H by 2H.
- **Avoiding two-torsion:** these are odd prime-order groups and have no nonidentity
  rational 2-torsion.
- **Canonical sign or point compression:** all H use even y, but the published G parities
  are mixed; doubling does not eliminate the ± ambiguity.
- **Making G a generator:** every nonidentity point already generates a prime-order group.
- **Reducing generic ECDLP risk:** multiplication by 2 is a public group automorphism and
  provides no such benefit.

## Assessment

The evidence now weighs against the strongest “cosmetic laundering implies malicious
intent” interpretation. A legacy `derive U, then multiply by a small cofactor` pipeline,
combined with a 160-bit-era source value, can explain the form of the construction
without a cryptanalytic motive. But it does not fully close the case: using 2 instead of
the actual cofactor 1, reusing a 152-bit core, and omitting the generation transcript all
remain unexplained design choices.

The most defensible wording is:

> Doubling probably reflects an undocumented point-generation or presentation convention
> inherited from cofactor-clearing workflows. It predictably obscures the source-point
> structure, but no evidence establishes that obscuring the structure was the purpose.

## Searches that did not produce an explanation

- Public SEC 2 versions 1.0 and 2.0 and SEC 1's point-selection procedure.
- Certicom ECC Challenge point-generation algorithms.
- FIPS/NIST curve-generation appendices and binary Koblitz cofactor conventions.
- Public patent searches involving Certicom, Koblitz curves, base points, and doubling.
- Indexed SECG/IETF mailing-list material, standards discussions, and contemporary source
  trees.
- Exact searches for the shared core and the secp224k1/secp256k1 source coordinate.

No recovered source attributes the choice to an identified designer or records the
original seed, tool, or selection transcript.
