"""CLI: sample the next question from the KG catalog and materialize it as Harbor.

Usage:
    uv run python -m data_gen.next_question \
        --artifacts-dir artifacts --context-dir generated_tasks \
        --out-dir generated_tasks --model anthropic/claude-sonnet-4-5
"""

from __future__ import annotations

import uuid
from pathlib import Path

from data_gen.catalog import load_catalog
from data_gen.harbor import materialize_harbor_task
from data_gen.inference_config import OpenAICompatibleConfig
from data_gen.question_gen import generate_question
from data_gen.question_sampler import sample_entry, sample_entry_via_retrieval


def _load_context(context_dir: Path | None) -> list[str]:
    """Reads every previously generated task's instruction.md as prior context."""
    if context_dir is None or not context_dir.is_dir():
        return []
    return [path.read_text() for path in sorted(context_dir.glob("*/instruction.md"))]


def build_next_question(
    artifacts_dir: Path,
    out_dir: Path,
    context_dir: Path | None = None,
    model: str | None = None,
    raw_model: str | None = None,
    query: str | None = None,
    kg_db_path: Path | None = None,
) -> Path:
    """Samples one catalog entry, generates its full spec, and writes it as Harbor.

    Args:
        artifacts_dir: Path to the tmax-data-gen/artifacts/ YAML catalog.
        out_dir: Directory the new task's subdirectory is created under.
        context_dir: Directory of previously generated Harbor tasks (each a
            subdirectory with an instruction.md) to avoid repeating.
        model: Model ID to route through the configured OpenAI-compatible
            endpoint (see .env's OPENAI_BASE_URL/OPENAI_API_KEY and
            data_gen/config/inference.yaml for available IDs). Mutually
            exclusive with `raw_model`; defaults to OPENAI_MODEL, then the
            config's `default_model`, when neither is given.
        raw_model: A full LiteLLM model string used verbatim (e.g.
            "anthropic/claude-sonnet-4-5"), bypassing the OpenAI-compatible
            endpoint entirely. Mutually exclusive with `model`.
        query: When given, the catalog entry is picked via
            `sample_entry_via_retrieval` (embedding search over the KG)
            instead of uniform random `sample_entry`; requires `kg_db_path`.
            The query and retrieved triplets are printed and recorded in
            the task's task_meta.json under "retrieval".
        kg_db_path: Path to the Kùzu database built by `kg_builder`.
            Required when `query` is given.

    Returns:
        Path to the newly created Harbor task directory.
    """
    if model and raw_model:
        raise ValueError("Pass at most one of `model` (OpenAI-compatible endpoint) or `raw_model` (direct LiteLLM), not both.")
    if query and kg_db_path is None:
        raise ValueError("`kg_db_path` is required when `query` is given.")

    if raw_model:
        litellm_model, extra_kwargs = raw_model, {}
    else:
        inference_config = OpenAICompatibleConfig.from_env(model=model)
        litellm_model, extra_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    catalog = load_catalog(artifacts_dir)

    retrieval_meta = None
    if query:
        retrieved = sample_entry_via_retrieval(catalog, query, kg_db_path)
        sample = retrieved.entry
        print(f"Retrieval query: {query!r}")
        for match in retrieved.matches:
            print(f"  {match.node_type} {match.node_id!r} (similarity={match.similarity:.3f})")
            for triplet in match.triplets:
                print(f"    {triplet}")
        retrieval_meta = {
            "query": retrieved.query,
            "matches": [
                {
                    "node_type": match.node_type,
                    "node_id": match.node_id,
                    "similarity": match.similarity,
                    "triplets": [str(triplet) for triplet in match.triplets],
                }
                for match in retrieved.matches
            ],
        }
    else:
        sample = sample_entry(catalog)

    context = _load_context(context_dir)
    question = generate_question(sample, model=litellm_model, context=context, extra_kwargs=extra_kwargs)

    task_name = f"{sample.domain.id}-{sample.primitive.id}-{uuid.uuid4().hex[:8]}"
    return materialize_harbor_task(question, out_dir / task_name, task_name, retrieval=retrieval_meta)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("artifacts"))
    parser.add_argument("--out-dir", type=Path, default=Path("generated_tasks"))
    parser.add_argument("--context-dir", type=Path, default=None)
    parser.add_argument(
        "--model", type=str, default=None, help="Model ID routed through the configured OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--raw-model", type=str, default=None, help="Full LiteLLM model string, bypassing the OpenAI-compatible endpoint."
    )
    parser.add_argument(
        "--query", type=str, default=None, help="Natural-language query to retrieve the catalog entry from the KG."
    )
    parser.add_argument(
        "--kg-db-path", type=Path, default=Path("data_gen/kg.db"), help="Kùzu database path; required with --query."
    )
    args = parser.parse_args()

    task_dir = build_next_question(
        args.artifacts_dir,
        args.out_dir,
        args.context_dir,
        model=args.model,
        raw_model=args.raw_model,
        query=args.query,
        kg_db_path=args.kg_db_path,
    )
    print(f"Wrote Harbor task to {task_dir}")
