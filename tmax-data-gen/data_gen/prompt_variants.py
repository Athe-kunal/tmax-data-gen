"""Create and load public prompt variants for an immutable Harbor task.

The task's setup, hidden truth, and verifier stay unchanged. A variant only
changes the text delivered to the solving agent, which makes precise and vague
benchmark results comparable for the same task case.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import litellm

from data_gen.inference_config import OpenAICompatibleConfig
from data_gen.weave_logger import weave_op

PRECISE_VARIANT_ID = "precise-v1"
_PROMPTS_DIR = "prompts"
_VAGUE_SYSTEM_TEMPLATE = """You rewrite an existing software task into a short, realistic user request.

Return only the rewritten request. Do not solve the task. Do not invent facts,
files, requirements, constraints, or acceptance criteria. Keep the user's
observable goal, but omit implementation detail and exact formatting details
where a normal human would not know them. The result may be ambiguous. It must
not mention hidden tests, ground truth, or this rewrite instruction.

Prompt style: {style}

Style guidance:
- symptom-only: describe observed symptoms and desired recovery, not the fix.
- goal-only: describe the outcome the user wants with little technical detail.
- suspected-cause: include a plausible but unverified user diagnosis.
- sparse-context: provide a short request with limited context.
"""


@dataclass(frozen=True)
class PromptVariant:
    """One public instruction rendered for a single immutable task case."""

    id: str
    kind: str
    style: str
    text: str
    path: Path
    source_instruction_sha256: str
    text_sha256: str
    generated_at: str | None = None
    generator_model: str | None = None


def _sha256(text: str | bytes) -> str:
    payload = text.encode() if isinstance(text, str) else text
    return hashlib.sha256(payload).hexdigest()


def task_case_hash(task_dir: Path) -> str:
    """Hashes the task state that must remain equal across prompt variants."""
    required = ("instruction.md", "tests/test.sh", "tests/test_final_state.py")
    digest = hashlib.sha256()
    for relative_path in required:
        path = task_dir / relative_path
        if not path.is_file():
            raise FileNotFoundError(f"Task case is missing {path}")
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    metadata = json.loads((task_dir / "task_meta.json").read_text())
    immutable_metadata = {
        key: value
        for key, value in metadata.items()
        if key not in {"prompt_variants", "task_case_sha256"}
    }
    digest.update(b"task_meta.json\0")
    digest.update(json.dumps(immutable_metadata, sort_keys=True, separators=(",", ":")).encode())
    setup_path = task_dir / "environment" / "setup.sh"
    if setup_path.is_file():
        digest.update(b"environment/setup.sh\0")
        digest.update(setup_path.read_bytes())
    return digest.hexdigest()


def _variant_metadata(task_dir: Path) -> dict[str, dict]:
    meta_path = task_dir / "task_meta.json"
    metadata = json.loads(meta_path.read_text())
    variants = metadata.get("prompt_variants", {})
    if not isinstance(variants, dict):
        raise ValueError(f"prompt_variants in {meta_path} must be an object")
    return variants


def load_prompt_variant(task_dir: Path, variant_id: str = PRECISE_VARIANT_ID) -> PromptVariant:
    """Loads a public prompt variant without exposing private task truth."""
    canonical_path = task_dir / "instruction.md"
    if not canonical_path.is_file():
        raise FileNotFoundError(f"Task is missing {canonical_path}")
    canonical = canonical_path.read_text()
    source_hash = _sha256(canonical)

    if variant_id == PRECISE_VARIANT_ID:
        return PromptVariant(
            id=PRECISE_VARIANT_ID,
            kind="precise",
            style="complete-specification",
            text=canonical,
            path=canonical_path,
            source_instruction_sha256=source_hash,
            text_sha256=source_hash,
        )

    variant_data = _variant_metadata(task_dir).get(variant_id)
    if variant_data is None:
        raise ValueError(f"Task {task_dir} has no prompt variant {variant_id!r}")
    relative_path = Path(variant_data["path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Prompt variant {variant_id!r} has an unsafe path")
    path = task_dir / relative_path
    if not path.is_file():
        raise FileNotFoundError(f"Prompt variant {variant_id!r} is missing {path}")
    text = path.read_text()
    if not text.strip():
        raise ValueError(f"Prompt variant {variant_id!r} is empty")
    if variant_data.get("source_instruction_sha256") != source_hash:
        raise ValueError(f"Prompt variant {variant_id!r} was created for a different precise instruction")
    text_hash = _sha256(text)
    if variant_data.get("text_sha256") != text_hash:
        raise ValueError(f"Prompt variant {variant_id!r} does not match its recorded hash")
    return PromptVariant(
        id=variant_id,
        kind=variant_data["kind"],
        style=variant_data["style"],
        text=text,
        path=path,
        source_instruction_sha256=source_hash,
        text_sha256=text_hash,
        generated_at=variant_data.get("generated_at"),
        generator_model=variant_data.get("generator_model"),
    )


@weave_op
def render_vague_prompt(
    precise_prompt: str,
    style: str,
    model: str | None = None,
    raw_model: str | None = None,
    max_tokens: int = 1_500,
) -> tuple[str, str]:
    """Renders a vague public prompt from public text only.

    The caller deliberately passes only ``instruction.md``. Private truth,
    verifier code, and setup data never enter this model call.
    """
    if model and raw_model:
        raise ValueError("Pass at most one of model or raw_model")
    if raw_model:
        resolved_model, kwargs = raw_model, {}
    else:
        config = OpenAICompatibleConfig.from_env(model=model)
        resolved_model, kwargs = config.litellm_model(), config.litellm_kwargs()
    response = litellm.completion(
        model=resolved_model,
        messages=[
            {"role": "system", "content": _VAGUE_SYSTEM_TEMPLATE.format(style=style)},
            {"role": "user", "content": precise_prompt},
        ],
        temperature=0.4,
        max_tokens=max_tokens,
        **kwargs,
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise ValueError("Prompt-variant model returned an empty response")
    return text, resolved_model


def create_vague_variant(
    task_dir: Path,
    style: str,
    model: str | None = None,
    raw_model: str | None = None,
    overwrite: bool = False,
) -> PromptVariant:
    """Writes one vague variant and records its provenance in task metadata."""
    precise = load_prompt_variant(task_dir)
    variant_id = f"vague-{style}-v1"
    filename = f"{variant_id}.md"
    output_path = task_dir / _PROMPTS_DIR / filename
    if output_path.exists() and not overwrite:
        raise FileExistsError(f"Prompt variant already exists at {output_path}")

    text, resolved_model = render_vague_prompt(precise.text, style, model, raw_model)
    output_path.parent.mkdir(exist_ok=True)
    output_path.write_text(text + "\n")

    meta_path = task_dir / "task_meta.json"
    metadata = json.loads(meta_path.read_text())
    variants = metadata.setdefault("prompt_variants", {})
    variants[variant_id] = {
        "kind": "vague",
        "style": style,
        "path": str(Path(_PROMPTS_DIR) / filename),
        "source_instruction_sha256": precise.source_instruction_sha256,
        "text_sha256": _sha256(text + "\n"),
        "generated_at": datetime.now(UTC).isoformat(),
        "generator_model": resolved_model,
    }
    metadata["task_case_sha256"] = task_case_hash(task_dir)
    meta_path.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n")
    return load_prompt_variant(task_dir, variant_id)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--task-dir", type=Path, required=True)
    parser.add_argument("--style", choices=("symptom-only", "goal-only", "suspected-cause", "sparse-context"), required=True)
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    variant = create_vague_variant(
        args.task_dir,
        args.style,
        model=args.model,
        raw_model=args.raw_model,
        overwrite=args.overwrite,
    )
    print(f"created {variant.id} at {variant.path}")


if __name__ == "__main__":
    main()
