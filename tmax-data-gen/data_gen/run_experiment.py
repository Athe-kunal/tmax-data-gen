"""Run matched precise and vague prompt evaluations and persist every outcome.

Example:
    uv run python -m data_gen.run_experiment \
        --tasks-dir gold_tasks --variants precise-v1 vague-symptom-only-v1 \
        --run-id minimax-prompt-robustness-v1 --model MiniMaxAI/MiniMax-M3
"""

from __future__ import annotations

import argparse
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

from data_gen.experiment_store import ExperimentStore
from data_gen.inference_config import OpenAICompatibleConfig
from data_gen.prompt_variants import load_prompt_variant
from data_gen.rollout import run_rollout


def discover_task_dirs(tasks_dir: Path) -> list[Path]:
    """Returns direct child Harbor task directories in a deterministic order."""
    if not tasks_dir.is_dir():
        raise NotADirectoryError(tasks_dir)
    return sorted(path for path in tasks_dir.iterdir() if (path / "task_meta.json").is_file())


def _solver_label(model: str | None, raw_model: str | None) -> str:
    if raw_model:
        return raw_model
    return OpenAICompatibleConfig.from_env(model=model).litellm_model()


def run_experiment(
    *,
    tasks_dir: Path,
    db_path: Path,
    run_id: str,
    variants: list[str],
    repetitions: int,
    environment: str,
    model: str | None,
    raw_model: str | None,
    agent_config: dict,
) -> None:
    if model and raw_model:
        raise ValueError("Pass at most one of model or raw_model")
    if repetitions < 1:
        raise ValueError("repetitions must be at least 1")
    if len(set(variants)) != len(variants):
        raise ValueError("variants must not contain duplicates")

    task_dirs = discover_task_dirs(tasks_dir)
    if not task_dirs:
        raise ValueError(f"No Harbor tasks found under {tasks_dir}")
    store = ExperimentStore(db_path)
    try:
        store.register_experiment(run_id, _solver_label(model, raw_model), environment, agent_config)
        for task_dir in task_dirs:
            case = store.register_task_case(task_dir)
            for variant_id in variants:
                variant = load_prompt_variant(task_dir, variant_id)
                store.register_prompt_variant(case, variant)
                for repetition in range(repetitions):
                    started_at = datetime.now(UTC).isoformat()
                    start = time.monotonic()
                    try:
                        result = run_rollout(
                            task_dir,
                            environment=environment,
                            agent_config=agent_config,
                            model=model,
                            raw_model=raw_model,
                            prompt_variant_id=variant_id,
                        )
                    except Exception as error:
                        store.record_rollout(
                            run_id=run_id,
                            case=case,
                            variant=variant,
                            repetition=repetition,
                            started_at=started_at,
                            finished_at=datetime.now(UTC).isoformat(),
                            status="error",
                            duration_seconds=time.monotonic() - start,
                            error_message=f"{type(error).__name__}: {error}",
                        )
                        print(f"error task={case.id} variant={variant_id} repetition={repetition}: {error}")
                        continue
                    store.record_rollout(
                        run_id=run_id,
                        case=case,
                        variant=variant,
                        repetition=repetition,
                        started_at=started_at,
                        finished_at=datetime.now(UTC).isoformat(),
                        status="completed",
                        reward=result.reward,
                        duration_seconds=time.monotonic() - start,
                        verifier_stdout=result.verifier_stdout,
                        agent_exit=result.agent_exit,
                    )
                    print(
                        f"completed task={case.id} variant={variant_id} repetition={repetition} reward={result.reward}"
                    )
    finally:
        store.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks-dir", type=Path, required=True)
    parser.add_argument("--db-path", type=Path, default=Path("runs/tmax_results.sqlite"))
    parser.add_argument("--run-id", type=str, default=None)
    parser.add_argument("--variants", nargs="+", default=["precise-v1", "vague-symptom-only-v1"])
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--environment", choices=("sandbox", "daytona"), default="sandbox")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    parser.add_argument("--step-limit", type=int, default=0)
    parser.add_argument("--cost-limit", type=float, default=0.0)
    args = parser.parse_args()
    run_experiment(
        tasks_dir=args.tasks_dir,
        db_path=args.db_path,
        run_id=args.run_id or f"experiment-{uuid.uuid4().hex[:12]}",
        variants=args.variants,
        repetitions=args.repetitions,
        environment=args.environment,
        model=args.model,
        raw_model=args.raw_model,
        agent_config={"step_limit": args.step_limit, "cost_limit": args.cost_limit},
    )


if __name__ == "__main__":
    main()
