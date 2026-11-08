# SWE-bench lab: results

## Status (2026-11-07 ~20:30 MST) - pilot NOT completed
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
| lucet-coder-4b-omega | django__django-11790 | 0 | >40 min (killed) | no | no (no patch; not evaluated) |

## Resume
    cd /home/mirai/projects/swebench-lab
    ./run_pilot.sh        # waits for the gate, runs, evaluates; log in runs/pilot-lucet.pilot.log
Outputs: `runs/pilot-lucet/preds.json`, `runs/pilot-lucet/<id>/<id>.traj.json`, `runs/pilot-lucet/eval/`, `runs/pilot-lucet.docker_df.txt`.

## Hours per instance
Not estimated yet (no measured run).

## Attempt log (pilot, django__django-11790, lucet-coder-4b-omega)
1. 19:33 MST, gate opened after 241 s. Run failed at 277 s with `ModuleNotFoundError: No module named 'mcp'`, raised by litellm's proxy catalog import. No model call was made (trajectory has 3 messages). Eval then scored an empty patch (not a model result). Fixed by `uv pip install mcp` in .venv. Log: `runs/pilot-lucet.attempt1-mcp-missing.pilot.log`.
2. 19:44 MST, rerun (gate open, 0 cases). Container started 19:45. The agent never returned: no trajectory, no preds entry, no steps completed, and no docker exec process after 19:45. At 20:25 MST the router's lucet-coder llama-server was at 584% CPU. I killed my driver and container at ~20:26 MST. Log: `runs/pilot-lucet.attempt2-hang.pilot.log`.
   - Not yet diagnosed. Likely a model request that did not return (generation not capped, or litellm timeout not hit). The router is not ours to stop; that llama-server may still be generating.
   - Also during attempt 2 a duplicate driver was started by mistake and killed (two containers removed).

## Hours per instance
Not estimable from one measured run. Attempt 1 produced no model work; attempt 2 hung for >40 min on its first step.

## Next steps (not done)
- Check the router's lucet-coder request timing and whether generation is capped (max_tokens is not set in configs/local-router.yaml).
- Add a per-request timeout / max_tokens to model_kwargs and rerun the pilot.
