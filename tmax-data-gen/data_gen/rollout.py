"""Runs a full agent rollout against a materialized Harbor task in a remote
sandbox, then executes the task's verifier and reports reward.

This is the "Check difficulty / Solve the question" step from the pipeline
design: rather than trusting an LLM-authored <truth> and test suite blindly,
the task is actually executed end to end. Wraps `harness.run_agent`, so the
entire agent trajectory - every tool call and every underlying model
completion - traces to Weave exactly like question generation does
(`data_gen.weave_logger`); `run_rollout` itself is also `@weave_op`-decorated
so the verifier's reward and stdout show up as call attributes for manual
review.

Backend-agnostic by construction: everything here - installing pytest,
writing the verifier files, running it, reading back the result - goes
through the environment's own `execute()` (the same interface every
mini-swe-agent environment implements), never a backend-specific SDK call
directly. That's what lets `environment="sandbox"` (W&B/CoreWeave) and
`environment="daytona"` work through the exact same code path; adding a
third backend later only means registering it in `harness._ENVIRONMENTS`.

Usage:
    uv run python -m data_gen.rollout \
        --task-dir generated_tasks/<task> --model anthropic/claude-sonnet-4-5 \
        --environment sandbox
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from data_gen.env_exec import read_file as _read_file
from data_gen.env_exec import run as _run
from data_gen.env_exec import write_file as _write_file
from data_gen.harbor import resolve_base_image
from data_gen.harness import _ENVIRONMENTS, run_agent
from data_gen.inference_config import OpenAICompatibleConfig  # also loads .env via python-dotenv on import
from data_gen.weave_logger import weave_op

_INSTALL_PYTEST_CMD = (
    "apt-get update && apt-get install -y --no-install-recommends python3 python3-pip "
    "&& (python3 -m pip install --no-cache-dir --break-system-packages pytest "
    "|| python3 -m pip install --no-cache-dir pytest)"
)

_AGENT_WORKDIR = "/home/user"
_TESTS_DIR = "/tests"

_SANDBOX_ENVIRONMENTS = ("sandbox", "daytona")
_IMAGE_KWARG = {"sandbox": "container_image", "daytona": "image"}


@dataclass(frozen=True)
class RolloutResult:
    """The outcome of one rollout against a Harbor task."""

    task_name: str
    reward: float
    verifier_stdout: str
    agent_exit: dict


@weave_op
def run_rollout(
    task_dir: Path,
    environment: Literal["sandbox", "daytona"] = "sandbox",
    container_image: str | None = None,
    agent_config: dict | None = None,
    model: str | None = None,
    raw_model: str | None = None,
) -> RolloutResult:
    """Solves and verifies one Harbor task inside a fresh remote sandbox.

    Args:
        task_dir: A directory materialized by `data_gen.harbor.materialize_harbor_task`.
        environment: "sandbox" (W&B/CoreWeave) or "daytona".
        container_image: Public image to start the sandbox from. Defaults to
            the task's language's resolved base image (see
            `data_gen.harbor.resolve_base_image`) - never the task's own
            `environment/Dockerfile`, since these backends pull a public
            image rather than building one.
        agent_config: Overrides for the agent config, e.g.
            `{"step_limit": 15, "cost_limit": 0.5}` to bound a rollout - both
            default to unlimited (0) in mini-swe-agent's own defaults.
        model: Model ID to route through the configured OpenAI-compatible
            endpoint (see .env's OPENAI_BASE_URL/OPENAI_API_KEY - same
            config `data_gen.next_question` uses). Mutually exclusive with
            `raw_model`; defaults to OPENAI_MODEL, then the config's
            `default_model`, when neither is given.
        raw_model: A full LiteLLM model string used verbatim (e.g.
            "anthropic/claude-sonnet-4-5"), bypassing the OpenAI-compatible
            endpoint entirely. Mutually exclusive with `model`.

    Returns:
        The RolloutResult: reward (1.0 pass / 0.0 fail, per tests/test.sh),
        the verifier's pytest output, and the agent's raw exit dict.
    """
    if environment not in _SANDBOX_ENVIRONMENTS:
        raise ValueError(f"environment must be one of {_SANDBOX_ENVIRONMENTS}, got {environment!r}")
    if model and raw_model:
        raise ValueError("Pass at most one of `model` (OpenAI-compatible endpoint) or `raw_model` (direct LiteLLM), not both.")

    if raw_model:
        litellm_model, model_kwargs = raw_model, {}
    else:
        inference_config = OpenAICompatibleConfig.from_env(model=model)
        litellm_model, model_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    task_meta = json.loads((task_dir / "task_meta.json").read_text())
    instruction = (task_dir / "instruction.md").read_text()
    image = container_image or resolve_base_image(task_meta["language"], None)

    env = _ENVIRONMENTS[environment](**{_IMAGE_KWARG[environment]: image})
    try:
        _run(env, _INSTALL_PYTEST_CMD, timeout=300)
        _run(env, f"mkdir -p {_AGENT_WORKDIR}")

        # Materializes the task's "given" initial state (input files,
        # datasets, services) before the agent starts - without this, the
        # agent has nothing to work from but its own guess at what that data
        # looks like, which then mismatches the verifier's truth-derived
        # expectations regardless of how well the task itself is solved.
        setup_script = task_meta.get("setup_script")
        if setup_script:
            _run(env, setup_script, timeout=300)

        # Verifier files live outside the agent's working directory so it
        # can't read its own test assertions - same no-leakage convention
        # `question_gen`'s <task>/<truth> split already follows.
        _write_file(env, f"{_TESTS_DIR}/test.sh", (task_dir / "tests" / "test.sh").read_bytes())
        _write_file(env, f"{_TESTS_DIR}/test_final_state.py", (task_dir / "tests" / "test_final_state.py").read_bytes())

        agent_exit = run_agent(
            instruction,
            litellm_model,
            environment=environment,
            environment_kwargs={"sandbox": env.sandbox, "cwd": _AGENT_WORKDIR},
            agent_config=agent_config,
            model_kwargs=model_kwargs,
        )

        _run(env, f"bash {_TESTS_DIR}/test.sh")  # test.sh always exits 0 by design; reward is in reward.txt
        reward = float(_read_file(env, "/logs/verifier/reward.txt").strip())
        verifier_stdout = _read_file(env, "/logs/verifier/test-stdout.txt")

        return RolloutResult(
            task_name=task_meta["task_name"], reward=reward, verifier_stdout=verifier_stdout, agent_exit=agent_exit
        )
    finally:
        env.cleanup()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument(
        "--model", type=str, default=None, help="Model ID routed through the configured OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--raw-model", type=str, default=None, help="Full LiteLLM model string, bypassing the OpenAI-compatible endpoint."
    )
    parser.add_argument("--environment", choices=_SANDBOX_ENVIRONMENTS, default="sandbox")
    parser.add_argument("--container-image", type=str, default=None)
    parser.add_argument("--step-limit", type=int, default=0, help="Max agent steps (0 = unlimited).")
    parser.add_argument("--cost-limit", type=float, default=0.0, help="Max agent cost in USD (0 = unlimited).")
    args = parser.parse_args()

    result = run_rollout(
        args.task_dir,
        environment=args.environment,
        container_image=args.container_image,
        agent_config={"step_limit": args.step_limit, "cost_limit": args.cost_limit},
        model=args.model,
        raw_model=args.raw_model,
    )
    print(f"reward={result.reward} task={result.task_name}")
    print(result.verifier_stdout)
