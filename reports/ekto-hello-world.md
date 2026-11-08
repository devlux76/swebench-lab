# qwen3-coder-30b-ekto-q4 in mini-swe-agent: hello-world per language

Date: 2026-11-07 (MST). Harness: mini-swe-agent 2.4.6 `mini` CLI, tool-calling, LOCAL environment (no docker), one fresh empty dir per task. Step limit 20. Each run is one fresh agent; tasks run strictly one at a time.

## Results

| language | pass | compiler errors | compiler warnings | steps | wall s | prompt tok | completion tok | prefill tok/s | gen tok/s |
|---|---|---|---|---|---|---|---|---|---|
| Python (`python3`) | yes | n/a | n/a | 6 | 120.0 | 7805 | 412 | 23.51 | 6.90 |
| TypeScript (`bun hello.ts`) | yes | n/a | n/a | 8 | 105.1 | 11324 | 490 | 31.86 | 7.62 |
| JavaScript (`bun hello.js`) | yes | n/a | n/a | 7 | 154.8 | 9666 | 476 | 17.75 | 5.31 |
| Elixir (`elixir hello.exs`) | yes | n/a | n/a | 10 | 227.8 | 14940 | 638 | 14.72 | 4.81 |
| Rust (`rustc hello.rs`, then `./hello`) | yes | 0 | 0 | 6 | 159.6 | 7880 | 413 | 18.28 | 4.39 |
| Bash (`bash hello.sh`) | yes | n/a | n/a | 7 | 179.5 | 9590 | 468 | 14.33 | 4.85 |
| C++ (`g++ hello.cpp`, then `./hello`) | yes | 0 | 0 | 11 | 245.2 | 17862 | 706 | 17.13 | 4.65 |

Totals: **7/7 pass**. Steps 55 (= model calls). Wall 1192.0 s (19.9 min). Prompt tokens 79067, completion tokens 3603.

Throughput, all requests pooled: prefill **18.39 tok/s** (8242 uncached prompt tokens / 448.2 s), generation **5.23 tok/s** (3603 tokens / 688.7 s).
Mean of per-task figures: prefill **19.65 tok/s**, generation **5.50 tok/s**. Per-request means (mean of the router's per-request rates, averaged over tasks): prefill 15.27, generation 5.51.

## How each number was measured

- Wall: shell timestamps (`date +%s.%N`) before and after the `mini` process. Includes Python startup (~1 s).
- Steps and model calls: assistant messages in the saved trajectory; both equal `info.model_stats.api_calls`. Every run ended with exit status `Submitted`.
- Prompt and completion tokens: sum of `usage` in each assistant response in the trajectory. Prompt tokens include cached tokens.
- Prefill and generation tok/s: the router's per-request `timings` object, which mini-swe-agent kept in each trajectory (`extra.response.timings`). Prefill uses `prompt_n` / `prompt_ms`, so **cached prompt tokens (`cache_n`) are excluded** from prefill; this is why prefill rates look low on long conversations. Generation uses `predicted_n` / `predicted_ms`.
- Pass/fail: an independent judge script (not the agent's claim) ran each file in a judge directory: compile step if needed, then execute; pass requires file present, compile success, exit 0, and stdout exactly `Hello, world!` plus one newline. Judge outputs: `runs/ekto-hello/judge/`.
- Compiler errors/warnings: lines matching `error` / `warning` in the compiler's stderr with default flags. "n/a" = interpreted language with no compile step (bun does not type-check TypeScript, so 0 type errors there is not evidence).

## Failures

None. All seven passed on independent judging.

Observed artifact (not a failure): in every trajectory the final `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` shows `"action was not executed"` as its observation. The command did run and mini-swe-agent raised `Submitted` (exit status `Submitted`); the observation is a logging placeholder because `execute_actions` appends outputs only after the command returns.

## Skipped / not run

No language was skipped; all seven toolchains were present (Python 3.14.4, bun 1.4.4, node 22.22.1 (version check only, not used for any task or judging), Elixir 1.20.4, rustc 1.93.1, g++ 15.2.0, bash 5.3.9).

Task text: TypeScript and JavaScript say "run it with bun" (operator correction). The other five use the generic text: "Compile it if the language needs compiling, run it, and confirm the output." The per-language run commands in the table are the judge's commands, not given to the model.

## Environment

- Model: `qwen3-coder-30b-ekto-q4` (llama.cpp router alias; `openai/qwen3-coder-30b-ekto-q4` via litellm), llama-server build `llama-6a1a7b304-cpu`.
- Quant: Q4_K_M (GGUF `Q4_K - Medium`), `/home/mirai/models/gguf/qwen3-coder-30b-ekto/qwen3-coder-30b-ekto-Q4_K_M.gguf`, 30.5B params, 18.55 GB.
- Context: 32768 (router preset `ctx-size`); model trained at 262144.
- Threads 6; batch 512; ubatch 512; parallel 1; cache-ram 2048 MiB. CPU only (`--device none`, `-ngl 0`).
- Sampling (router preset and request): temperature 0.7, top_p 0.8, top_k 20, repetition_penalty 1.05. The request also sends these explicitly (top_k and repetition_penalty via `extra_body`); the preset already had identical values, so the effective settings are the same either way.
- Request cap: `max_tokens` 4096, litellm `timeout` 900 s (`configs/local-router.yaml`). No request hit either limit.
- Machine: MacBook Pro T2 running Linux, Intel i9-8950HK (6 cores / 12 threads, AVX2, no AVX-512), 29 GB RAM (about 7 GB available during the run), no GPU offload. CPU governor not changed.
- Other models: all other router entries were `unloaded`; only the qwen model was loaded for the whole session.
- Vulkan embedder: unit `ranger-embed.service` (`/home/mirai/.config/systemd/user/ranger-embed.service`, process `llama-39c25a1ac-vulkan/llama-server`, port 8091). Stopped at 22:51 MST for the benchmark and restarted at the end; it is active and its `/health` returns ok. ranger's embedding calls were unavailable during the window.

## Lab changes

- `configs/local-router.yaml`: adds `max_tokens` 4096, `timeout` 900, temperature 0.7, top_p 0.8, extra_body top_k 20 and repetition_penalty 1.05 (same overlay also used by the SWE-bench runner).
- `configs/hello-local.yaml` (new): step limit 20, cost limit 0, for the local hello-world runs.
- `lab.env`: `export MSWEA_CONFIGURED=1`. Without it, `mini` runs the first-time setup wizard, reads stdin, and aborts before any model call. The earlier attempts that hit this wizard made no model calls.

Trajectories (`runs/ekto-hello/<lang>.traj.json`), logs, and judge outputs are under `runs/` (gitignored).

## Reproduce

    cd /home/mirai/projects/swebench-lab && . ./lab.env
    .venv/bin/mini -y --exit-immediately -c mini.yaml -c configs/local-router.yaml -c configs/hello-local.yaml \
      --environment-class local -m openai/qwen3-coder-30b-ekto-q4 -t "<task>" -o runs/ekto-hello/<lang>.traj.json
