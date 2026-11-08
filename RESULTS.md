# SWE-bench lab: results

## Status (2026-11-07 ~19:32 MST)
- Environment: done (mini-swe-agent 2.4.6, swebench 5.0.2, litellm 1.108.3, Python 3.12 in `.venv`).
- Subset: `subset50.txt` (50 ids from MariusHobbhahn/swe-bench-verified-mini). Pilot id = `django__django-11790`.
- Pilot image pulled: `docker.io/swebench/sweb.eval.x86_64.django_1776_django-11790:latest` (4.18 GB).
- Pilot run: NOT YET EXECUTED. Blocked by the WAIT GATE. At 19:31 MST one trailblazer case was open/running:
  `vortex-d09cbbb04962e4083fa7783809ea0adfe30a655b7f930632177650a12c9cf4d9` (sojourney, tests for fireRules).
  `run_pilot.sh` is polling the gate every 60 s and gives up at 20:09 MST (45 min from 19:24 MST).
- The router was NOT touched by this lab yet. `lucet-coder-4b-omega` was already loaded when checked.

## Pilot table
| model | instance | steps | wall time | patch? | resolved? |
|---|---|---|---|---|---|
| lucet-coder-4b-omega | django__django-11790 | - | - | - | - (pending gate) |

## Resume
    cd /home/mirai/projects/swebench-lab
    ./run_pilot.sh        # waits for the gate, runs, evaluates; log in runs/pilot-lucet.pilot.log
Outputs: `runs/pilot-lucet/preds.json`, `runs/pilot-lucet/<id>/<id>.traj.json`, `runs/pilot-lucet/eval/`, `runs/pilot-lucet.docker_df.txt`.

## Hours per instance
Not estimated yet (no measured run).

## Haiku via Claude Code CLI (run `haiku-cli-5`, branch `haiku-cli-backend`)

Backend: `claude_cli_model.py` (`ClaudeCliModel`), config `configs/claude-cli.yaml`, wrapper `run_haiku_cli.sh`.
Each query runs `claude -p --model haiku --output-format json --tools "" --safe-mode --no-session-persistence --permission-mode dontAsk --system-prompt <system + bash-fence contract>` with the transcript on stdin; timeout 300 s, 1 retry. The CLI has no tools, so each ```bash fenced block in the reply becomes one bash tool call. Otherwise swebench.yaml prompts and environment are unchanged; step_limit 50.

Smoke test (local env, "create hello.txt containing hi, then submit"): 2 model calls, `exit_status: Submitted`, hello.txt written, list-price cost $0.00099.

| instance | status | steps (model calls) | wall s | input tok (incl. cache) | output tok | reported cost (USD, list) | patch submitted | resolved |
|---|---|---|---|---|---|---|---|---|
| django__django-11790 | Submitted | 12 | 577 | 73,819 | 13,188 | 0.0194 | yes (829 chars) | not evaluated |
| django__django-11815 | pending (image pulled on retry 4; run not yet done) | - | - | - | - | - | - | - |
| django__django-11848 | pending (docker pull failed) | - | - | - | - | - | - | - |
| django__django-11880 | pending (docker pull failed) | - | - | - | - | - | - | - |
| django__django-11885 | pending (docker pull failed) | - | - | - | - | - | - | - |

Notes:
- Wall = model init to last model reply (includes container start, excludes eval).
- 11790: 13 CLI attempts for 12 calls; one call hit the 300 s timeout and the retry succeeded.
- Costs are the CLI's `total_cost_usd` (list-price estimate), not a measured plan charge.
- The first batch attempt was SIGTERMed at 19:44:13 by an unidentified sender (not this lab's code). It was re-run from scratch.
- Instances 11815/11848/11880/11885 in the first batch failed at `docker run` (Docker Hub blob/auth errors, transient), before any model call; they were re-queued.
- Evaluation is BLOCKED: `swebench.harness.run_evaluation` (5.0.2) fails with `KeyError: 'image'` on the princeton-nlp/SWE-bench_Verified rows (`make_test_spec` needs `image` and `eval_script` fields the public dataset lacks). The NOTES eval command does not work as written; `resolved` is unknown for all rows.

Resume:
    cd /home/mirai/projects/swebench-lab-haiku
    # pull the remaining images (retry), then re-run the four pending ids with --redo-existing
    # (see the batch command in this section's run; filter ^(django__django-11815|django__django-11848|django__django-11880|django__django-11885)$)
