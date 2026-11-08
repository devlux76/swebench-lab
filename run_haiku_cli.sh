#!/usr/bin/env bash
# usage: run_haiku_cli.sh <run_name> <filter_regex> [slice]
# Runs mini-swe-agent's SWE-bench batch runner with the Claude Code CLI backend (Haiku, tools disabled).
set -euo pipefail
cd "$(dirname "$0")"
LAB=/home/mirai/projects/swebench-lab   # main checkout: holds .venv
RUN="$1"; FILTER="$2"; SLICE="${3:-}"
export PYTHONPATH="$(pwd)" OPENAI_API_KEY=dummy MSWEA_COST_TRACKING=ignore_errors MSWEA_SILENT_STARTUP=1 MSWEA_CONFIGURED=true
OUT="runs/$RUN"
mkdir -p "$OUT"
ARGS=(--subset verified --split test --filter "$FILTER" -o "$OUT"
      -c swebench.yaml -c configs/claude-cli.yaml
      -w 1 -m claude-cli-haiku)
[ -n "$SLICE" ] && ARGS+=(--slice "$SLICE")
"$LAB/.venv/bin/mini-extra" swebench "${ARGS[@]}"
