#!/usr/bin/env bash
# usage: run_swebench.sh <model_id> <run_name> <filter_regex> [slice]
# Runs mini-swe-agent's SWE-bench batch runner against the local llama.cpp router.
set -euo pipefail
cd /home/mirai/projects/swebench-lab
. ./lab.env
MODEL="$1"; RUN="$2"; FILTER="$3"; SLICE="${4:-}"
OUT="runs/$RUN"
mkdir -p "$OUT"
ARGS=(--subset verified --split test --filter "$FILTER" -o "$OUT"
      -c swebench.yaml -c configs/local-router.yaml
      -w 1 -m "openai/$MODEL")
[ -n "$SLICE" ] && ARGS+=(--slice "$SLICE")
.venv/bin/mini-extra swebench "${ARGS[@]}"
