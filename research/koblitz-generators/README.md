# Opaque Generators: a study of SECG Koblitz generator selection

This package contains the complete reproducible investigation summarized at
[sovereignsteak.com/projects/dlp-gen](https://sovereignsteak.com/projects/dlp-gen/).
It preserves both the initially blocked cybersecurity-oriented prompt and the accepted
higher-assurance reframing, along with the scripts, deterministic data, machine-readable
results, incremental notes, and final report.

The verified coordinate pattern is a provenance concern. The experiments found no
credible evidence of a base-specific ECDLP shortcut; see `FINAL_REPORT.md` for the
scope and limitations of that conclusion.

## Reproduction

Run the complete reproducible pipeline from this directory:

```bash
python3 scripts/verify_sec2.py
python3 scripts/reverse_engineer.py
python3 scripts/generate_corpus.py --count 2000 --seed dlp-gen-corpus-v1
python3 scripts/analyze_corpus.py
env DOT_SAGE=/tmp/dlp_gen_sage sage sage/further_analysis.py
python3 scripts/summarize_sage.py
python3 scripts/analyze_affixes.py
# Expanded relation scans may be sharded with --start/--count.
python3 scripts/expanded_relations.py --count 200 --factor-base-size 48 \
  --limit 500000 --output results/relations.jsonl
python3 scripts/analyze_relations.py
env DOT_SAGE=/tmp/dlp_gen_sage sage sage/verify_relations.py
# Three-summand witnesses and resultant-defined Semaev f4 verification:
python3 scripts/expanded_relations.py --count 100 --arity 3 \
  --factor-base-size 12 --limit 500000 --output results/relations_f4.jsonl
python3 scripts/analyze_relations.py --input results/relations_f4.jsonl \
  --output results/relations_f4_analysis.json
env DOT_SAGE=/tmp/dlp_gen_sage sage sage/verify_f4.py \
  --input results/relations_f4.jsonl --groebner-limit 3
python3 -m unittest discover -s tests -v
```

Corpus generation and SEC verification need only Python. Analysis needs NumPy.
`scripts/derive_sec2_generators.py` is the reference multi-generator derivation; use a
public seed fixed after the protocol and curve choices are committed.

The checked-in corpus was generated in four deterministic 500-row shards. Its merge
and exact invocation details are documented in `REPORT.md`.

The later attack-oriented follow-up, including isolated Gröbner workers and replicated
GLV coefficient-box tests, is documented in `ATTACK_FOLLOWUP.md`.

The sourced investigation of plausible historical reasons for publishing `G=2H` is in
`DOUBLING_RATIONALE_RESEARCH.md`.
