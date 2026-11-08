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
