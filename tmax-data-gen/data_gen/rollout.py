"""Runs a full agent rollout against a materialized Harbor task in a
W&B/CoreWeave Sandbox, then executes the task's verifier and reports reward.

This is the "Check difficulty / Solve the question" step from the pipeline
design: rather than trusting an LLM-authored <truth> and test suite blindly,
the task is actually executed end to end. Wraps `harness.run_agent` with
`environment="sandbox"` (see `data_gen.sandbox_environment`), so the entire
agent trajectory - every tool call and every underlying model completion -
traces to Weave exactly like question generation does (`data_gen.
weave_logger`); `run_rollout` itself is also `@weave_op`-decorated so the
verifier's reward and stdout show up as call attributes for manual review.

Usage:
    uv run python -m data_gen.rollout \
        --task-dir generated_tasks/<task> --model anthropic/claude-sonnet-4-5
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import cwsandbox

from data_gen.harbor import resolve_base_image
from data_gen.harness import run_agent
from data_gen.weave_logger import weave_op

_INSTALL_PYTEST_CMD = (
    "apt-get update && apt-get install -y --no-install-recommends python3 python3-pip "
    "&& (python3 -m pip install --no-cache-dir --break-system-packages pytest "
    "|| python3 -m pip install --no-cache-dir pytest)"
)

_AGENT_WORKDIR = "/home/user"
_TESTS_DIR = "/tests"


@dataclass(frozen=True)
class RolloutResult:
    """The outcome of one rollout against a Harbor task."""

    task_name: str
    reward: float
    verifier_stdout: str
    agent_exit: dict


def _write_verifier(sandbox: cwsandbox.Sandbox, task_dir: Path) -> None:
    sandbox.exec(["mkdir", "-p", _TESTS_DIR]).result()
    sandbox.write_file(f"{_TESTS_DIR}/test.sh", (task_dir / "tests" / "test.sh").read_bytes()).result()
    sandbox.write_file(
        f"{_TESTS_DIR}/test_final_state.py", (task_dir / "tests" / "test_final_state.py").read_bytes()
    ).result()


@weave_op
def run_rollout(task_dir: Path, model_name: str, container_image: str | None = None) -> RolloutResult:
    """Solves and verifies one Harbor task inside a fresh Sandbox.

    Args:
        task_dir: A directory materialized by `data_gen.harbor.materialize_harbor_task`.
        model_name: LiteLLM model string for the solving agent.
        container_image: Public image to start the sandbox from. Defaults to
            the task's language's resolved base image (see
            `data_gen.harbor.resolve_base_image`) - never the task's own
            `environment/Dockerfile`, since Sandboxes pull a public image
            rather than building one.

    Returns:
        The RolloutResult: reward (1.0 pass / 0.0 fail, per tests/test.sh),
        the verifier's pytest output, and the agent's raw exit dict.
    """
    task_meta = json.loads((task_dir / "task_meta.json").read_text())
    instruction = (task_dir / "instruction.md").read_text()
    image = container_image or resolve_base_image(task_meta["language"], None)

    sandbox = cwsandbox.Sandbox.run(
        "sleep", "infinity", container_image=image, auth=cwsandbox.AuthStrategy.WANDB
    ).wait()
    try:
        sandbox.exec(["bash", "-lc", _INSTALL_PYTEST_CMD], timeout_seconds=300, check=True).result()
        sandbox.exec(["mkdir", "-p", _AGENT_WORKDIR]).result()

        # Verifier files live outside the agent's working directory so it
        # can't read its own test assertions - same no-leakage convention
        # `question_gen`'s <task>/<truth> split already follows.
        _write_verifier(sandbox, task_dir)

        agent_exit = run_agent(
            instruction,
            model_name,
            environment="sandbox",
            environment_kwargs={"sandbox": sandbox, "cwd": _AGENT_WORKDIR},
        )

        sandbox.exec(["bash", f"{_TESTS_DIR}/test.sh"], cwd=_TESTS_DIR).result()
        reward = float(sandbox.read_file("/logs/verifier/reward.txt").result().decode().strip())
        verifier_stdout = sandbox.read_file("/logs/verifier/test-stdout.txt").result().decode(errors="replace")

        return RolloutResult(
            task_name=task_meta["task_name"], reward=reward, verifier_stdout=verifier_stdout, agent_exit=agent_exit
        )
    finally:
        sandbox.stop(missing_ok=True)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--container-image", type=str, default=None)
    args = parser.parse_args()

    result = run_rollout(args.task_dir, args.model, container_image=args.container_image)
    print(f"reward={result.reward} task={result.task_name}")
    print(result.verifier_stdout)
