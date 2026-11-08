"""mini-swe-agent model backend that runs Claude through the Claude Code CLI.

Selected from a config with `model.model_class: claude_cli_model.ClaudeCliModel`
(needs PYTHONPATH to include the lab directory).

Every query is one `claude -p --model haiku --output-format json` call with ALL
built-in tools disabled (`--tools ""`), so the CLI cannot act on the machine. The
agent's bash tool is therefore carried in text: the tool contract is appended to
the system prompt, and each ```bash fenced block in the reply becomes one bash
tool call (the same shape mini-swe-agent's tool-call path already consumes).
"""

import json
import re
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from pydantic import BaseModel

from minisweagent.exceptions import FormatError
from minisweagent.models import GLOBAL_MODEL_STATS
from minisweagent.models.utils.actions_toolcall import format_toolcall_observation_messages, parse_toolcall_actions

LAB_DIR = Path(__file__).resolve().parent

TOOL_CONTRACT = """
You have one tool, `bash`, which runs a bash command in the task's shell. Shell state (cwd, variables) does not persist between commands. You have no other tools and cannot call any; do not claim to run anything yourself.

To run a command, put it in a fenced code block whose language tag is exactly `bash`. Each such block is one bash tool call. The system executes the blocks and returns each output in the next message. Fenced blocks with any other language tag are not executed.
""".strip()

BASH_FENCE_RE = re.compile(r"^```bash[ \t]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE)


class ClaudeCliModelConfig(BaseModel):
    model_name: str
    """Name recorded in preds.json as model_name_or_path."""
    cli_model: str = "haiku"
    """Value passed to `claude --model`."""
    cli: str = "claude"
    timeout: int = 300
    """Seconds per CLI call."""
    retries: int = 1
    """Extra attempts after a failed CLI call (error, timeout, bad JSON)."""
    format_error_template: str = "{{ error }}"
    observation_template: str = (
        "{% if output.exception_info %}<exception>{{output.exception_info}}</exception>\n{% endif %}"
        "<returncode>{{output.returncode}}</returncode>\n<output>\n{{output.output}}</output>"
    )
    # Accepted so the builtin swebench.yaml model section can be merged in unchanged; ignored here.
    model_kwargs: dict[str, Any] = {}
    set_cache_control: str | None = None
    cost_tracking: str = "default"


class ClaudeCliModel:
    def __init__(self, **kwargs):
        self.config = ClaudeCliModelConfig(**kwargs)
        self.stats: dict[str, Any] = {
            "n_calls": 0,
            "cli_attempts": 0,
            "retries": 0,
            "input_tokens": 0,
            "output_tokens": 0,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
            "cost_usd": 0.0,
            "cli_duration_s": 0.0,
            "t_init": time.time(),
            "t_last_reply": None,
        }

    # ---- transcript -------------------------------------------------------

    def _serialize_messages(self, messages: list[dict]) -> tuple[str, str]:
        """Return (system_prompt, transcript). The transcript ends with the latest user/tool output."""
        system = ""
        parts = []
        for i, m in enumerate(messages):
            role = m.get("role")
            content = m.get("content") or ""
            if not isinstance(content, str):
                content = json.dumps(content)
            if role == "system" and i == 0:
                system = content
                continue
            if role == "exit":
                continue
            header = {"user": "USER", "assistant": "ASSISTANT", "tool": "TOOL OUTPUT (bash)"}.get(
                role, str(role).upper()
            )
            parts.append(f"=== {header} ===\n{content}")
        return system, "\n\n".join(parts)

    # ---- CLI call ---------------------------------------------------------

    def _call_cli(self, system_prompt: str, prompt: str) -> dict:
        cmd = [
            self.config.cli,
            "-p",
            "--model", self.config.cli_model,
            "--output-format", "json",
            "--tools", "",
            "--safe-mode",
            "--no-session-persistence",
            "--permission-mode", "dontAsk",
            "--system-prompt", system_prompt,
        ]  # fmt: skip
        last_err: Exception | None = None
        for attempt in range(1 + self.config.retries):
            self.stats["cli_attempts"] += 1
            if attempt:
                self.stats["retries"] += 1
            try:
                proc = subprocess.run(
                    cmd, input=prompt, capture_output=True, text=True, timeout=self.config.timeout, cwd=LAB_DIR
                )
                if proc.returncode != 0:
                    raise RuntimeError(f"claude exited {proc.returncode}: {proc.stderr.strip()[-500:]}")
                data = json.loads(proc.stdout)
                if data.get("is_error") or data.get("subtype") != "success" or "result" not in data:
                    raise RuntimeError(
                        f"claude reported error: subtype={data.get('subtype')} "
                        f"result={str(data.get('result'))[:300]}"
                    )
                return data
            except (subprocess.TimeoutExpired, RuntimeError, json.JSONDecodeError) as e:
                last_err = e
                print(f"[claude_cli_model] attempt {attempt + 1} failed: {e}", file=sys.stderr)
        raise RuntimeError(f"claude CLI failed after {1 + self.config.retries} attempts: {last_err}")

    # ---- mini-swe-agent model contract ------------------------------------

    def _parse_actions(self, content: str, stop_reason: str | None) -> list[dict]:
        blocks = [b.strip() for b in BASH_FENCE_RE.findall(content)]
        tool_calls = [
            SimpleNamespace(
                id=f"call_{i}",
                function=SimpleNamespace(name="bash", arguments=json.dumps({"command": b})),
            )
            for i, b in enumerate(blocks)
            if b
        ]
        # has_tool_calls is supplied by parse_toolcall_actions itself; passing it again breaks the render.
        finish_reason = "length" if stop_reason == "max_tokens" else "stop"
        return parse_toolcall_actions(
            tool_calls,
            format_error_template=self.config.format_error_template,
            template_kwargs={"finish_reason": finish_reason},
        )

    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        system, transcript = self._serialize_messages(messages)
        system_prompt = f"{system}\n\n{TOOL_CONTRACT}" if system else TOOL_CONTRACT
        data = self._call_cli(system_prompt, transcript)

        usage = data.get("usage") or {}
        in_plain = int(usage.get("input_tokens") or 0)
        cache_create = int(usage.get("cache_creation_input_tokens") or 0)
        cache_read = int(usage.get("cache_read_input_tokens") or 0)
        out_tokens = int(usage.get("output_tokens") or 0)
        cost = float(data.get("total_cost_usd") or 0.0)
        duration_s = float(data.get("duration_ms") or 0.0) / 1000.0

        self.stats["n_calls"] += 1
        self.stats["input_tokens"] += in_plain + cache_create + cache_read
        self.stats["output_tokens"] += out_tokens
        self.stats["cache_creation_input_tokens"] += cache_create
        self.stats["cache_read_input_tokens"] += cache_read
        self.stats["cost_usd"] += cost
        self.stats["cli_duration_s"] += duration_s
        self.stats["t_last_reply"] = time.time()

        GLOBAL_MODEL_STATS.add(cost)
        cost_output = {
            "cost": cost,
            "usage": {
                "input_tokens": in_plain + cache_create + cache_read,
                "output_tokens": out_tokens,
                "cache_creation_input_tokens": cache_create,
                "cache_read_input_tokens": cache_read,
            },
        }
        content = data.get("result") or ""
        try:
            actions = self._parse_actions(content, data.get("stop_reason"))
        except FormatError as e:
            e.messages[0]["extra"].update(cost_output)
            e.messages[0]["extra"]["response"] = data
            raise
        return {
            "role": "assistant",
            "content": content,
            "extra": {
                "actions": actions,
                "response": data,
                **cost_output,
                "timestamp": time.time(),
            },
        }

    def format_message(self, **kwargs) -> dict:
        return kwargs

    def format_observation_messages(
        self, message: dict, outputs: list[dict], template_vars: dict | None = None
    ) -> list[dict]:
        actions = message.get("extra", {}).get("actions", [])
        return format_toolcall_observation_messages(
            actions=actions,
            outputs=outputs,
            observation_template=self.config.observation_template,
            template_vars=template_vars,
        )

    def get_template_vars(self, **kwargs) -> dict[str, Any]:
        return self.config.model_dump()

    def serialize(self) -> dict:
        return {
            "info": {
                "config": {
                    "model": self.config.model_dump(mode="json"),
                    "model_type": f"{self.__class__.__module__}.{self.__class__.__name__}",
                },
                "claude_cli_stats": self.stats,
            }
        }
