#!/usr/bin/env bash
# Semantic tier probe: one model call per (rule, file), high thinking, JSON out.
# Usage: semantic_check.sh RULE_DIR FILE [MODEL]
set -euo pipefail
rule_dir=$1 file=$2 model=${3:-sonnet}
prompt=$(cat <<EOF
You check ONE refactoring rule against ONE Python file. Report every occurrence; do not report anything else.

RULE (from the owner's rulebook):
$(cat "$rule_dir/rule.md")

FILE: $file
$(nl -ba "$file")

Answer with JSON only, no prose: {"hits": [{"line": <line of the def>, "symbol": "<name>", "why": "<one sentence>"}], "checked_symbols": ["<every function or method you examined>"]}
EOF
)
omp -p --model "$model" --thinking high --no-tools "$prompt"
