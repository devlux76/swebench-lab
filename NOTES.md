# SWE-bench lab: notes

Versions (installed in .venv, Python 3.12): mini-swe-agent 2.4.6, swebench 5.0.2, litellm 1.108.3.

## mini-swe-agent batch runner (facts from installed source)
- Entry: `mini-extra swebench` -> `minisweagent/run/benchmarks/swebench.py`.
- Dataset: `--subset verified --split test` (maps to princeton-nlp/SWE-bench_Verified). `--filter <regex>` on instance_id, `--slice a:b`, `-w` workers.
- Output: `<-o DIR>/preds.json` (dict keyed by instance_id: model_name_or_path, instance_id, model_patch) and `<DIR>/<id>/<id>.traj.json`. Existing ids are skipped unless `--redo-existing`.
- Config: `-c swebench.yaml` (builtin, resolved by name) then `-c configs/local-router.yaml` overlay, then `-m openai/<id>`. Later `-c` overrides earlier ones (recursive merge).
- Model: litellm, tool-calling (bash tool). Local endpoint = `openai/<id>` + `model_kwargs.api_base`. `OPENAI_API_KEY=dummy` (litellm requires a key).
- Cost: `MSWEA_COST_TRACKING=ignore_errors`. Without it, an unpriced model (cost <= 0) raises RuntimeError. Default `cost_limit` = 3.0 (no effect at cost 0).
- Limits: default `step_limit` = 250; overridden to 50 in configs/local-router.yaml.
- Sampling: swebench.yaml sets no temperature (only drop_params), so the router/server default applies.
- Environment: docker, cwd `/testbed`, 60 s per command, image `docker.io/swebench/sweb.eval.x86_64.<id with __ replaced by _1776_>:latest` (lowercased). Agent submits by printing `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` followed by `patch.txt`.
- Observation template truncates output > 10000 chars.

## swebench harness (5.0.2)
- `python -m swebench.harness.run_evaluation -d princeton-nlp/SWE-bench_Verified -s test -p <preds.json> -i <id> --max_workers 1 -id <run_id> --report_dir <dir>`.
- Empty `model_patch` instances are dropped from evaluation (counted as not resolved).
- `--report_dir` defaults to `.` (cwd), so pass it explicitly.
- Default `--timeout` 1800 s per instance.

## Subset
- `subset50.txt` = sorted instance_ids of `MariusHobbhahn/swe-bench-verified-mini` (50 rows, split `test`). Pilot = first line.
