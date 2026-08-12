#!/usr/bin/env bash
set -euo pipefail
if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "usage: $0 FACTOR_BASE_SIZE [INPUT_JSONL] [OUTPUT_PREFIX]" >&2
  exit 2
fi
factor_base_size="$1"
input_jsonl="${2:-data/high_value_corpus.jsonl}"
output_prefix="${3:-high_value_b${factor_base_size}}"
for shard in {0..7}; do
  start=$((shard * 63))
  python3 scripts/expanded_relations.py --input "$input_jsonl" \
    --start "$start" --count 63 --arity 3 --factor-base-size "$factor_base_size" --limit 500000 \
    --output "results/${output_prefix}_${shard}.jsonl" &
done
for shard in {8..15}; do
  start=$((504 + (shard - 8) * 62))
  python3 scripts/expanded_relations.py --input "$input_jsonl" \
    --start "$start" --count 62 --arity 3 --factor-base-size "$factor_base_size" --limit 500000 \
    --output "results/${output_prefix}_${shard}.jsonl" &
done
wait
python3 scripts/merge_corpus.py "results/${output_prefix}.jsonl" results/${output_prefix}_{0..15}.jsonl
