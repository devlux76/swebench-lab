# Evaluation follow-up for Terminal-RSI

Proposed protocol, 2026-11-10. No benchmark was run for this note.
Source: [Terminal-RSI v3](https://arxiv.org/html/2610.22192v3), §§3.1, 3.5, 5
and Appendices E–F. See the [paper findings and training proposal](../../lfm3-coding/docs/terminal-rsi.md).

## Apply to this lab

Use the existing `subset50.txt`, prediction artifacts and per-instance trajectories
described in [NOTES](../NOTES.md). Pin the actual instance list, dataset revision,
container image digest, runner/evaluator versions, model or adapter hash, prompt,
sampling settings and resource limits for each comparison. A filename alone is
not a frozen benchmark. Apply this protocol to the sibling `swebench-lab-haiku`
only when its settings and task manifest are also recorded.

Compare base LFM3 with a language adapter using identical inference allowances.
Start with a bounded pilot after the training queue and shared inference policy
permit it. Do not change the router or launch competing inference from this note.
For adapter selection, use a development task set. Keep the final task set out
of training, runbook creation and repeated checkpoint decisions, checking repository
and duplicate overlap with the fine-tuning catalogue before interpreting results.

## Report each attempt

- Task/repeat IDs and whether dispatch, agent execution and grading completed.
- Patch presence and applicability; official harness resolution result.
- Protected regression checks and required implementation constraints, where
  independently enforceable. If architecture matters, test it explicitly rather
  than infer it from output equivalence.
- Terminal reason: resolved, agent failure, budget exhausted, infrastructure
  failure or not attempted. Keep raw evidence; a missing result is never success.
- Turns, prompt/generated tokens, wall time and total compute, including retries.
  Store partial-check diagnostics separately from the strict resolution flag.

Use the frozen scheduled denominator and show coverage/status counts. Report an
operational success rate including scheduled infrastructure failures, alongside
any explicitly defined model-only subset. Do not quietly drop empty patches,
timeouts or missing results; reconcile evaluator exclusions against the manifest.

If affordable, use three independent repeats on a common task list. Report average
attempt success and pass@3 separately: the latter counts a task solved in any
repeat and costs three attempts. One repeat is acceptable as an explicitly small
pilot. Preserve per-task results and paired base/adapter comparisons; do not claim
statistical superiority from a small score difference or from repeated inference
alone. Hardware differences and incomplete runs belong in the report.

**Completion criterion:** all scheduled attempts have an auditable disposition,
strict outcomes come from the unchanged evaluator, and the summary can be
recomputed from the manifest and raw reports. Historical rows in `RESULTS.md`
retain their original status; this note does not retroactively establish success.
