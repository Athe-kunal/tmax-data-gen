"""Runs a multi-turn rollout: one persistent sandbox and one persistent
mini-swe-agent conversation, across up to `max_turns` questions.

Turn 0 (cold start) is seeded from tmax's own published RL data corpus
(`data_gen.tmax_rl_seed`) rather than generated - a real, pre-vetted task to
bootstrap the sandbox and conversation, sidestepping the small-model
`<truth>`-parsing failures a fresh LLM generation can hit with nothing yet
to condition on. This is a bootstrap only: every turn after that is the
fully dynamic retrieval+generation loop below, which is where the actual
"dynamic data" this pipeline exists for comes from.

Each turn after the first:
  1. Question Agent decides the next question - `sample_entry_via_retrieval`
     with a query derived from the trajectory so far (the just-completed
     turn's task description), then `question_gen.generate_question` writes
     that entry's task/truth/tests.
  2. NPC Agent delivers it - `generate_question`'s system prompt already
     requires the <task> text be "framed from the persona's perspective"
     (see question_gen.py), so no separate roleplay call is needed: the
     generated task description *is* the NPC's line, injected as the next
     user-role message.
  3. The solving agent (mini-swe-agent) steps until it submits (or hits a
     limit) - onto the SAME `agent.messages`, never reset. Turn 1 uses
     `DefaultAgent.run()` as-is. Turns after that can't reuse `run()`: it
     unconditionally does `self.messages = []`. `_continue_with_task` below
     is `run()`'s inner loop with that reset removed, built only from
     `DefaultAgent`'s public API (`add_messages`, `step`, `config`,
     `handle_uncaught_exception`) - no monkey-patching of mini-swe-agent.
  4. That turn's verifier runs in the SAME sandbox; reward recorded.

The full trajectory (every turn's sample, question, agent exit, and reward)
is returned; `run_multi_turn_rollout` is `@weave_op`-decorated so it - and
every model/tool call nested inside it - traces to Weave for manual review.

Usage:
    uv run python -m data_gen.multi_turn_rollout \
        --artifacts-dir artifacts --kg-db-path data_gen/kg.db \
        --environment daytona --max-turns 5
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from minisweagent.agents.default import DefaultAgent
from minisweagent.exceptions import FormatError, InterruptAgentFlow

from data_gen.catalog import Catalog, load_catalog
from data_gen.env_exec import read_file as _read_file
from data_gen.env_exec import run as _run
from data_gen.env_exec import write_file as _write_file
from data_gen.harbor import TEST_SH, resolve_base_image
from data_gen.harness import _ENVIRONMENTS, build_agent
from data_gen.inference_config import OpenAICompatibleConfig  # also loads .env via python-dotenv on import
from data_gen.question_gen import GeneratedQuestion, generate_question
from data_gen.question_sampler import SampledEntry, sample_entry_via_retrieval
from data_gen.tmax_rl_seed import (
    apply_seed_environment,
    build_seed_question,
    build_seed_sample,
    extract_base_image,
    load_tmax_rl_dataset,
    pick_seed_row,
)
from data_gen.weave_logger import weave_op

_AGENT_WORKDIR = "/home/user"
_TESTS_DIR = "/tests"

_SANDBOX_ENVIRONMENTS = ("sandbox", "daytona")
_IMAGE_KWARG = {"sandbox": "container_image", "daytona": "image"}

_INSTALL_PYTEST_CMD = (
    "apt-get update && apt-get install -y --no-install-recommends python3 python3-pip "
    "&& (python3 -m pip install --no-cache-dir --break-system-packages pytest "
    "|| python3 -m pip install --no-cache-dir pytest)"
)


@dataclass(frozen=True)
class TurnResult:
    """The outcome of one question within a multi-turn rollout.

    Carries the full `GeneratedQuestion` (task/truth/tests) and this turn's
    exact message slice (from the question being posed through the agent's
    exit) - not just `agent_exit`'s summary - so a gold turn (see
    `data_gen.gold`) has everything needed to be replayed as a reference
    solution: the fully-specified task, its verifier, and the trajectory
    that solved it.
    """

    sample: SampledEntry
    question: GeneratedQuestion
    messages: list[dict]
    reward: float
    verifier_stdout: str
    agent_exit: dict

    @property
    def task_description(self) -> str:
        return self.question.task_description


@dataclass(frozen=True)
class TrajectoryResult:
    """The full multi-turn rollout: every turn, in order."""

    turns: list[TurnResult] = field(default_factory=list)


def _run_verifier(env, question: GeneratedQuestion) -> tuple[float, str]:
    """Writes this turn's verifier into the sandbox, runs it, returns (reward, stdout).

    Overwrites the previous turn's tests/ files - each turn's reward is read
    back synchronously right after running its own test.sh, before the next
    turn overwrites them, so no turn-indexed paths are needed.
    """
    _write_file(env, f"{_TESTS_DIR}/test.sh", TEST_SH.encode())
    _write_file(env, f"{_TESTS_DIR}/test_final_state.py", question.test_code.encode())
    _run(env, f"bash {_TESTS_DIR}/test.sh")
    reward = float(_read_file(env, "/logs/verifier/reward.txt").strip())
    verifier_stdout = _read_file(env, "/logs/verifier/test-stdout.txt")
    return reward, verifier_stdout


def _continue_with_task(agent: DefaultAgent, task_message: str) -> dict:
    """Injects `task_message` as a new user turn onto `agent`'s *existing*
    conversation and steps until it exits.

    This is `DefaultAgent.run()`'s inner loop with the `self.messages = []`
    reset removed, built only from `DefaultAgent`'s public API - the agent
    class itself is untouched.
    """
    agent.add_messages(agent.model.format_message(role="user", content=task_message))
    while True:
        try:
            agent.step()
            agent.n_consecutive_format_errors = 0
        except FormatError as e:
            agent.cost += e.messages[0].get("extra", {}).get("cost", 0.0)
            agent.n_consecutive_format_errors += 1
            if 0 < agent.config.max_consecutive_format_errors <= agent.n_consecutive_format_errors:
                agent.add_messages(
                    *e.messages,
                    {
                        "role": "exit",
                        "content": "RepeatedFormatError",
                        "extra": {"exit_status": "RepeatedFormatError", "submission": ""},
                    },
                )
            else:
                agent.add_messages(*e.messages)
        except InterruptAgentFlow as e:
            agent.add_messages(*e.messages)
        except Exception as e:
            agent.handle_uncaught_exception(e)
            raise
        finally:
            agent.save(agent.config.output_path)
        if agent.messages[-1].get("role") == "exit":
            break
    return agent.messages[-1].get("extra", {})


@weave_op
def run_multi_turn_rollout(
    artifacts_dir: Path,
    kg_db_path: Path,
    environment: Literal["sandbox", "daytona"] = "sandbox",
    container_image: str | None = None,
    max_turns: int = 5,
    agent_config: dict | None = None,
    model: str | None = None,
    raw_model: str | None = None,
) -> TrajectoryResult:
    """Runs up to `max_turns` questions as one continuous agent/sandbox session.

    Args:
        artifacts_dir: Path to the tmax-data-gen/artifacts/ YAML catalog.
        kg_db_path: Path to the Kùzu database built by `kg_builder`.
        environment: "sandbox" (W&B/CoreWeave) or "daytona".
        container_image: Public image for the sandbox. Defaults to turn 1's
            sampled entry's language's resolved base image (see
            `data_gen.harbor.resolve_base_image`) and is then fixed for
            every subsequent turn in the rollout (one sandbox throughout).
        max_turns: Number of questions to ask in this rollout.
        agent_config: Overrides for the agent config, e.g.
            `{"cost_limit": 2.0}` - applies cumulatively across all turns
            (mini-swe-agent's own cost/step counters are never reset
            between turns, only between separate rollouts).
        model: Model ID routed through the configured OpenAI-compatible
            endpoint. Mutually exclusive with `raw_model`.
        raw_model: A full LiteLLM model string used verbatim, bypassing the
            OpenAI-compatible endpoint. Mutually exclusive with `model`.

    Returns:
        The TrajectoryResult: every turn's sample, question, agent exit, and reward.
    """
    if environment not in _SANDBOX_ENVIRONMENTS:
        raise ValueError(f"environment must be one of {_SANDBOX_ENVIRONMENTS}, got {environment!r}")
    if model and raw_model:
        raise ValueError("Pass at most one of `model` or `raw_model`, not both.")

    if raw_model:
        litellm_model, model_kwargs = raw_model, {}
    else:
        inference_config = OpenAICompatibleConfig.from_env(model=model)
        litellm_model, model_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    catalog: Catalog = load_catalog(artifacts_dir)
    tmax_rl_df = load_tmax_rl_dataset()
    turns: list[TurnResult] = []
    env = None
    agent: DefaultAgent | None = None

    try:
        for turn_index in range(max_turns):
            if turn_index == 0:
                # Cold start: bootstrap from tmax's own RL data, not a fresh
                # generation - see module docstring.
                seed_row = pick_seed_row(tmax_rl_df)
                sample = build_seed_sample(seed_row, catalog)
                question = build_seed_question(seed_row, sample)
            else:
                # 1. Question Agent: retrieve based on the trajectory so far.
                sample = sample_entry_via_retrieval(catalog, turns[-1].task_description, kg_db_path).entry
                question = generate_question(
                    sample,
                    model=litellm_model,
                    context=[t.task_description for t in turns],
                    extra_kwargs=model_kwargs,
                )

            # First turn only: start the sandbox + agent; later turns reuse both.
            if env is None:
                if turn_index == 0:
                    image = container_image or extract_base_image(seed_row["container_def"])
                else:
                    image = container_image or resolve_base_image(sample.language.id, sample.language.base_image)
                env = _ENVIRONMENTS[environment](**{_IMAGE_KWARG[environment]: image})
                _run(env, _INSTALL_PYTEST_CMD)
                _run(env, f"mkdir -p {_AGENT_WORKDIR}")
                if turn_index == 0:
                    apply_seed_environment(env, seed_row)
                agent = build_agent(
                    litellm_model,
                    environment=environment,
                    environment_kwargs={"sandbox": env.sandbox, "cwd": _AGENT_WORKDIR},
                    agent_config=agent_config,
                    model_kwargs=model_kwargs,
                )

            # 2. NPC Agent: the persona-framed <task> text *is* the delivery.
            messages_start = len(agent.messages)
            if turn_index == 0:
                agent_exit = agent.run(question.task_description)
            else:
                agent_exit = _continue_with_task(agent, question.task_description)
            turn_messages = agent.messages[messages_start:]

            # 3. Verify this turn in the same sandbox.
            reward, verifier_stdout = _run_verifier(env, question)

            turns.append(
                TurnResult(
                    sample=sample,
                    question=question,
                    messages=turn_messages,
                    reward=reward,
                    verifier_stdout=verifier_stdout,
                    agent_exit=agent_exit,
                )
            )
    finally:
        if env is not None:
            env.cleanup()

    return TrajectoryResult(turns=turns)


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--kg-db-path", type=Path, default=Path("data_gen/kg.db"))
    parser.add_argument("--environment", choices=_SANDBOX_ENVIRONMENTS, default="sandbox")
    parser.add_argument("--container-image", type=str, default=None)
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    parser.add_argument("--step-limit", type=int, default=0, help="Cumulative across all turns (0 = unlimited).")
    parser.add_argument("--cost-limit", type=float, default=0.0, help="Cumulative across all turns (0 = unlimited).")
    args = parser.parse_args()

    trajectory = run_multi_turn_rollout(
        args.artifacts_dir,
        args.kg_db_path,
        environment=args.environment,
        container_image=args.container_image,
        max_turns=args.max_turns,
        agent_config={"step_limit": args.step_limit, "cost_limit": args.cost_limit},
        model=args.model,
        raw_model=args.raw_model,
    )
    for i, turn in enumerate(trajectory.turns):
        print(f"--- turn {i}: reward={turn.reward} domain={turn.sample.domain.id} primitive={turn.sample.primitive.id} ---")
        print(turn.task_description[:200])
