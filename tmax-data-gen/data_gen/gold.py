"""Collects gold questions: fully-specified tasks (instruction + truth +
test suite) paired with a trajectory that actually solved them.

A turn from `data_gen.multi_turn_rollout` is "gold" when its reward meets
`gold_threshold` (default 1.0 - the verifier actually passed). Gold turns
are materialized as ordinary Harbor tasks (via `data_gen.harbor.
materialize_harbor_task`, so nothing about the task format is duplicated)
plus a `trajectory.json` holding the exact messages that solved it - the
reference solution for that task.

This step deliberately does NOT touch environment or question content -
noise injection (perturbing the environment/question for evaluation) is a
separate, later step that reads gold tasks as its input, not something
folded into collection.

Usage:
    uv run python -m data_gen.gold \
        --artifacts-dir artifacts --kg-db-path data_gen/kg.db \
        --environment daytona --max-turns 5 --out-dir gold_tasks
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path

from data_gen.harbor import materialize_harbor_task
from data_gen.multi_turn_rollout import TrajectoryResult, TurnResult, run_multi_turn_rollout

_TRAJECTORY_FORMAT = "mini-swe-agent-1.1"


def is_gold(turn: TurnResult, gold_threshold: float = 1.0) -> bool:
    return turn.reward >= gold_threshold


def materialize_gold_turn(turn: TurnResult, out_dir: Path) -> Path:
    """Writes one gold turn as a Harbor task plus its solving trajectory.

    Args:
        turn: A TurnResult with `turn.reward >= gold_threshold` (see `is_gold`).
        out_dir: Directory to create the task in (must not already exist).

    Returns:
        `out_dir`, now containing the standard Harbor task layout (see
        `data_gen.harbor.materialize_harbor_task`) plus `trajectory.json`.
    """
    materialize_harbor_task(turn.question, out_dir, out_dir.name)
    (out_dir / "trajectory.json").write_text(
        json.dumps(
            {
                "messages": turn.messages,
                "reward": turn.reward,
                "verifier_stdout": turn.verifier_stdout,
                "agent_exit": turn.agent_exit,
                "trajectory_format": _TRAJECTORY_FORMAT,
            },
            indent=2,
        )
    )
    return out_dir


def collect_gold_from_trajectory(trajectory: TrajectoryResult, out_dir: Path, gold_threshold: float = 1.0) -> list[Path]:
    """Materializes every gold turn in `trajectory` under `out_dir`.

    Args:
        trajectory: A completed TrajectoryResult (see `run_multi_turn_rollout`).
        out_dir: Directory each gold task's subdirectory is created under.
        gold_threshold: Minimum reward (see `is_gold`) for a turn to be kept.

    Returns:
        Paths to every materialized gold task directory, in turn order.
    """
    kept: list[Path] = []
    for turn in trajectory.turns:
        if not is_gold(turn, gold_threshold):
            continue
        task_name = f"{turn.sample.domain.id}-{turn.sample.primitive.id}-{uuid.uuid4().hex[:8]}"
        kept.append(materialize_gold_turn(turn, out_dir / task_name))
    return kept


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--kg-db-path", type=Path, default=Path("data_gen/kg.db"))
    parser.add_argument("--out-dir", type=Path, default=Path("gold_tasks"))
    parser.add_argument("--environment", choices=("sandbox", "daytona"), default="sandbox")
    parser.add_argument("--container-image", type=str, default=None)
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--gold-threshold", type=float, default=1.0)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    parser.add_argument("--step-limit", type=int, default=0)
    parser.add_argument("--cost-limit", type=float, default=0.0)
    parser.add_argument(
        "--agent-max-tokens",
        type=int,
        default=None,
        help="Max tokens per agent completion. Needed for reasoning models (e.g. GLM-5.2) - "
        "too small a default truncates before an action is produced.",
    )
    parser.add_argument(
        "--generation-max-tokens",
        type=int,
        default=None,
        help="Max tokens per question-generation completion. Same reasoning-model consideration "
        "as --agent-max-tokens, but for generate_question rather than solving.",
    )
    parser.add_argument(
        "--model-style",
        choices=("text", "toolcall"),
        default="text",
        help="'text' parses one markdown-fenced bash block; 'toolcall' uses native tool_calls "
        "(tools=[BASH_TOOL]). Pick per model based on observed behavior, not a fixed default - "
        "see data_gen.harness._MODEL_STYLES.",
    )
    args = parser.parse_args()

    result = run_multi_turn_rollout(
        args.artifacts_dir,
        args.kg_db_path,
        environment=args.environment,
        container_image=args.container_image,
        max_turns=args.max_turns,
        agent_config={"step_limit": args.step_limit, "cost_limit": args.cost_limit},
        model=args.model,
        raw_model=args.raw_model,
        model_style=args.model_style,
        agent_max_tokens=args.agent_max_tokens,
        generation_max_tokens=args.generation_max_tokens,
    )
    gold_paths = collect_gold_from_trajectory(result, args.out_dir, args.gold_threshold)

    print(f"{len(gold_paths)}/{len(result.turns)} turns were gold (reward >= {args.gold_threshold})")
    for path in gold_paths:
        print(f"  {path}")
