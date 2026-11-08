#!/usr/bin/env bash
# One end-to-end pilot: wait for the trailblazer gate, run lucet-coder-4b-omega on the
# first subset id, then evaluate the prediction with the official swebench harness.
set -uo pipefail
cd /home/mirai/projects/swebench-lab
MODEL=lucet-coder-4b-omega
RUN=pilot-lucet
ID=$(head -1 subset50.txt)
LOG=runs/$RUN.pilot.log
mkdir -p runs
log() { echo "$(date -Is) $*" | tee -a "$LOG"; }

# 1. WAIT GATE: no open/running trailblazer case, polled every 60 s, give up after 45 min.
start=$(date +%s)
while :; do
  n=$(sqlite3 /home/mirai/.local/share/trailblazer/cases.db "select count(*) from task_case where status in ('open','running')")
  log "gate open+running=$n"
  [ "$n" = "0" ] && break
  if [ $(( $(date +%s) - start )) -ge 2700 ]; then log "GATE_TIMEOUT"; exit 1; fi
  sleep 60
done
log "GATE_OPEN after $(( $(date +%s) - start ))s"

# 2. RUN
log "run start id=$ID model=$MODEL"
rm -rf "runs/$RUN"
t0=$(date +%s)
./run_swebench.sh "$MODEL" "$RUN" "^${ID}\$" > "runs/$RUN.run.out" 2>&1
rc=$?
t1=$(date +%s)
log "run done rc=$rc wall=$((t1-t0))s"

# 3. EVAL
log "eval start"
e0=$(date +%s)
.venv/bin/python -m swebench.harness.run_evaluation -d princeton-nlp/SWE-bench_Verified -s test \
  -p "runs/$RUN/preds.json" -i "$ID" --max_workers 1 -id "$RUN" --report_dir "runs/$RUN/eval" \
  > "runs/$RUN.eval.out" 2>&1
erc=$?
e1=$(date +%s)
log "eval done rc=$erc wall=$((e1-e0))s"
docker system df > "runs/$RUN.docker_df.txt" 2>&1
log "DONE"
