#!/usr/bin/env bash
set -euo pipefail
for shard in {0..7}; do
  start=$((shard * 63))
  python3 scripts/generate_high_value.py --start "$start" --count 63 --output "data/high_value_${shard}.jsonl" &
done
for shard in {8..15}; do
  start=$((504 + (shard - 8) * 62))
  python3 scripts/generate_high_value.py --start "$start" --count 62 --output "data/high_value_${shard}.jsonl" &
done
wait
python3 scripts/merge_corpus.py data/high_value_corpus.jsonl data/high_value_{0..15}.jsonl
