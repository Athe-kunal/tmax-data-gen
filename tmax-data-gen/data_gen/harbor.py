"""Materializes a GeneratedQuestion into a Harbor-format task directory.

Layout (matches the Harbor schema `tmax/rl_data/scripts/analyze/convert_to_harbor.py`
already targets, built here directly instead of via an Apptainer intermediate):

    <out_dir>/
        instruction.md          # the public <task> text - never contains <truth>
        task.toml
        task_meta.json          # provenance sidecar (includes truth) - NOT copied
                                 # into the container; for audit/debugging only
        environment/
            Dockerfile
        tests/
            test.sh
            test_final_state.py
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

from data_gen.question_gen import GeneratedQuestion

ORG_NAME = "tmax"

# All bases below are Debian-family images, so a uniform apt-get install works
# regardless of which one a task's language maps to. None of the catalog's
# language.yaml files set `base_image` today (see artifacts/languages/), so
# this is the deterministic fallback; a populated `base_image` always wins.
DEFAULT_BASE_IMAGES: dict[str, str] = {
    "python": "python:3.13-slim",
    "bash": "ubuntu:22.04",
    "c": "ubuntu:22.04",
    "cpp": "ubuntu:22.04",
    "rust": "rust:1.82-slim",
    "go": "golang:1.23",
    "multi-language": "ubuntu:22.04",
    "model-choice": "ubuntu:22.04",
}

TEST_SH = textwrap.dedent("""\
    #!/bin/bash
    set -e

    mkdir -p /logs/verifier

    cd /tests
    python3 -m pytest test_final_state.py -v 2>&1 | tee /logs/verifier/test-stdout.txt
    TEST_EXIT=${PIPESTATUS[0]}

    if [ $TEST_EXIT -eq 0 ]; then
        echo 1 > /logs/verifier/reward.txt
    else
        echo 0 > /logs/verifier/reward.txt
    fi

    exit 0
""")


def _escape_toml(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def resolve_base_image(language_id: str, base_image: str | None) -> str:
    """Resolves the public container image for a language.

    Also used by `data_gen.rollout` to pick the image a W&B Sandbox starts
    from, since Sandboxes pull a public image rather than building from the
    Dockerfile this module generates.
    """
    if base_image:
        return base_image
    if language_id not in DEFAULT_BASE_IMAGES:
        raise ValueError(
            f"No default base image for language {language_id!r} and none set in its catalog "
            f"entry; add one to DEFAULT_BASE_IMAGES or artifacts/languages/{language_id}.yaml"
        )
    return DEFAULT_BASE_IMAGES[language_id]


def _generate_dockerfile(language_id: str, base_image: str | None) -> str:
    """The verifier always runs as pytest (see `tests/test.sh`), regardless of
    the task's own language, so python3/pip/pytest are installed unconditionally
    on top of the language's base image."""
    return textwrap.dedent(f"""\
        FROM {resolve_base_image(language_id, base_image)}

        ENV DEBIAN_FRONTEND=noninteractive

        RUN apt-get update \\
            && apt-get install -y --no-install-recommends python3 python3-pip \\
            && rm -rf /var/lib/apt/lists/*
        RUN python3 -m pip install --no-cache-dir --break-system-packages pytest \\
            || python3 -m pip install --no-cache-dir pytest

        WORKDIR /home/user
    """)


def _generate_task_toml(question: GeneratedQuestion, task_name: str) -> str:
    sample = question.sample
    description = question.task_description.strip().splitlines()[0][:200]
    return textwrap.dedent(f"""\
        schema_version = "1.1"

        [task]
        name = "{ORG_NAME}/{task_name}"
        description = "{_escape_toml(description)}"

        [metadata]
        source = "tmax-data-gen knowledge graph"
        domain = "{_escape_toml(sample.domain.id)}"
        skill_type = "{_escape_toml(sample.skill_type.id)}"
        primitive_skill = "{_escape_toml(sample.primitive.id)}"
        persona = "{_escape_toml(sample.persona.id)}"
        language = "{_escape_toml(sample.language.id)}"
        generation_model = "{_escape_toml(question.model)}"

        [agent]
        timeout_sec = 600.0

        [verifier]
        timeout_sec = 120.0

        [environment]
        cpus = 1
        memory_mb = 2048
        allow_internet = true
    """)


def materialize_harbor_task(
    question: GeneratedQuestion, out_dir: Path, task_name: str, retrieval: dict | None = None
) -> Path:
    """Writes `question` to `out_dir` as a Harbor task. Returns `out_dir`.

    Args:
        question: The generated task/truth/test spec.
        out_dir: Directory to create the task in (must not already exist).
        task_name: Short identifier used in task.toml's `[task].name` and,
            typically, as `out_dir`'s basename.
        retrieval: When the sample was picked via `sample_entry_via_retrieval`,
            its provenance (query + retrieved triplets) to record in
            task_meta.json alongside the rest of the sample's ids. None when
            the sample came from plain random `sample_entry`.
    """
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} already exists")

    (out_dir / "environment").mkdir(parents=True)
    (out_dir / "tests").mkdir(parents=True)

    (out_dir / "instruction.md").write_text(question.task_description + "\n")
    (out_dir / "task.toml").write_text(_generate_task_toml(question, task_name))
    (out_dir / "environment" / "Dockerfile").write_text(
        _generate_dockerfile(question.sample.language.id, question.sample.language.base_image)
    )
    (out_dir / "tests" / "test.sh").write_text(TEST_SH)
    (out_dir / "tests" / "test_final_state.py").write_text(question.test_code + "\n")
    if question.setup_script:
        (out_dir / "environment" / "setup.sh").write_text(question.setup_script + "\n")

    meta = {
        "task_name": task_name,
        "domain": question.sample.domain.id,
        "skill_type": question.sample.skill_type.id,
        "primitive_skill": question.sample.primitive.id,
        "persona": question.sample.persona.id,
        "language": question.sample.language.id,
        "generation_model": question.model,
        "task_description": question.task_description,
        "truth": question.truth,
        "setup_script": question.setup_script,
    }
    if retrieval is not None:
        meta["retrieval"] = retrieval
    (out_dir / "task_meta.json").write_text(json.dumps(meta, indent=2))

    return out_dir
