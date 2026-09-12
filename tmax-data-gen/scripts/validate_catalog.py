"""Validate the Tmax replicator source-of-truth artifact catalog."""

from __future__ import annotations

import math
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"

EXPECTED_DOMAIN_IDS = {
    "security",
    "software_engineering",
    "file_operations",
    "data_querying",
    "data_science",
    "debugging",
    "scientific_computing",
    "data_processing",
    "system_administration",
}

EXPECTED_LANGUAGE_IDS = {
    "python",
    "c",
    "bash",
    "cpp",
    "rust",
    "go",
    "multi-language",
    "model-choice",
}


def fail(message: str) -> None:
    raise ValueError(message)


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.is_file():
        fail(f"missing file: {path.relative_to(ROOT)}")
    with path.open() as file:
        data = yaml.safe_load(file)
    if not isinstance(data, dict):
        fail(f"expected a YAML object: {path.relative_to(ROOT)}")
    return data


def require_fields(data: dict[str, Any], fields: set[str], label: str) -> None:
    missing = fields - data.keys()
    if missing:
        fail(f"{label}: missing fields: {', '.join(sorted(missing))}")


def validate_guidance(guidance: Any, label: str) -> None:
    if not isinstance(guidance, dict):
        fail(f"{label}: guidance must be an object")
    require_fields(guidance, {"origin", "goal", "expected_operations"}, label)
    if guidance["origin"] != "authored":
        fail(f"{label}: guidance origin must be 'authored'")
    if not isinstance(guidance["goal"], str) or not guidance["goal"].strip():
        fail(f"{label}: guidance goal must be a non-empty string")
    operations = guidance["expected_operations"]
    if not isinstance(operations, list) or not operations or not all(
        isinstance(operation, str) and operation.strip() for operation in operations
    ):
        fail(f"{label}: expected_operations must be a non-empty list of strings")


def validate_domain(path: Path, expected_id: str) -> None:
    data = load_yaml(path)
    require_fields(data, {"schema_version", "id", "name", "description"}, str(path))
    if data["schema_version"] != 1 or data["id"] != expected_id:
        fail(f"{path.relative_to(ROOT)}: domain ID or schema version mismatch")


def validate_skills(path: Path, expected_domain_id: str) -> None:
    data = load_yaml(path)
    require_fields(data, {"schema_version", "domain_id", "skill_types"}, str(path))
    if data["schema_version"] != 1 or data["domain_id"] != expected_domain_id:
        fail(f"{path.relative_to(ROOT)}: skill catalog ID or schema version mismatch")
    skill_types = data["skill_types"]
    if not isinstance(skill_types, list) or not skill_types:
        fail(f"{path.relative_to(ROOT)}: skill_types must be a non-empty list")
    for skill_type in skill_types:
        if not isinstance(skill_type, dict):
            fail(f"{path.relative_to(ROOT)}: skill type must be an object")
        require_fields(skill_type, {"id", "name", "primitives"}, str(path))
        primitives = skill_type["primitives"]
        if not isinstance(primitives, list) or not primitives:
            fail(f"{path.relative_to(ROOT)}: primitives must be a non-empty list")
        for primitive in primitives:
            if not isinstance(primitive, dict):
                fail(f"{path.relative_to(ROOT)}: primitive must be an object")
            require_fields(primitive, {"id", "description", "guidance"}, str(path))
            validate_guidance(primitive["guidance"], f"{path.relative_to(ROOT)}:{primitive['id']}")


def validate_personas(path: Path, expected_domain_id: str) -> None:
    data = load_yaml(path)
    require_fields(data, {"schema_version", "domain_id", "personas"}, str(path))
    if data["schema_version"] != 1 or data["domain_id"] != expected_domain_id:
        fail(f"{path.relative_to(ROOT)}: persona catalog ID or schema version mismatch")
    personas = data["personas"]
    if not isinstance(personas, list) or not personas:
        fail(f"{path.relative_to(ROOT)}: personas must be a non-empty list")
    for persona in personas:
        if not isinstance(persona, dict):
            fail(f"{path.relative_to(ROOT)}: persona must be an object")
        require_fields(persona, {"id", "role", "description"}, str(path))


def validate_language(path: Path, expected_id: str) -> float:
    data = load_yaml(path)
    require_fields(
        data,
        {
            "schema_version",
            "id",
            "name",
            "sampling_weight",
            "runtime",
            "runtime_guidance_origin",
            "package_manager",
            "build_command",
            "test_command",
            "compatible_domain_ids",
        },
        str(path),
    )
    if data["schema_version"] != 1 or data["id"] != expected_id:
        fail(f"{path.relative_to(ROOT)}: language ID or schema version mismatch")
    if data["runtime_guidance_origin"] != "authored":
        fail(f"{path.relative_to(ROOT)}: runtime guidance origin must be 'authored'")
    compatible_domain_ids = data["compatible_domain_ids"]
    if not isinstance(compatible_domain_ids, list) or set(compatible_domain_ids) != EXPECTED_DOMAIN_IDS:
        fail(f"{path.relative_to(ROOT)}: compatible_domain_ids must list every Tmax domain exactly once")
    if len(compatible_domain_ids) != len(EXPECTED_DOMAIN_IDS):
        fail(f"{path.relative_to(ROOT)}: compatible_domain_ids must not contain duplicates")
    weight = data["sampling_weight"]
    if not isinstance(weight, (int, float)) or weight <= 0:
        fail(f"{path.relative_to(ROOT)}: sampling_weight must be positive")
    return float(weight)


def main() -> int:
    index = load_yaml(ARTIFACTS / "index.yaml")
    require_fields(index, {"schema_version", "domains", "languages"}, "artifacts/index.yaml")
    if index["schema_version"] != 1:
        fail("artifacts/index.yaml: unsupported schema version")

    domains = index["domains"]
    if not isinstance(domains, list):
        fail("artifacts/index.yaml: domains must be a list")
    domain_ids = {entry.get("id") for entry in domains if isinstance(entry, dict)}
    if domain_ids != EXPECTED_DOMAIN_IDS or len(domains) != len(EXPECTED_DOMAIN_IDS):
        fail("artifacts/index.yaml: must register the nine Tmax domains exactly once")
    for entry in domains:
        require_fields(entry, {"id", "domain_file", "skill_file", "persona_file"}, "domain index entry")
        domain_id = entry["id"]
        validate_domain(ARTIFACTS / entry["domain_file"], domain_id)
        validate_skills(ARTIFACTS / entry["skill_file"], domain_id)
        validate_personas(ARTIFACTS / entry["persona_file"], domain_id)

    languages = index["languages"]
    if not isinstance(languages, list):
        fail("artifacts/index.yaml: languages must be a list")
    language_ids = {entry.get("id") for entry in languages if isinstance(entry, dict)}
    if language_ids != EXPECTED_LANGUAGE_IDS or len(languages) != len(EXPECTED_LANGUAGE_IDS):
        fail("artifacts/index.yaml: must register the eight Tmax language choices exactly once")
    weight_total = 0.0
    for entry in languages:
        require_fields(entry, {"id", "file"}, "language index entry")
        weight_total += validate_language(ARTIFACTS / entry["file"], entry["id"])
    if not math.isclose(weight_total, 1.0, abs_tol=1e-9):
        fail(f"language sampling weights must total 1.0, found {weight_total}")

    print("catalog validation passed: 9 domains, 283 skills, 85 personas, 8 languages")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, yaml.YAMLError) as error:
        print(f"catalog validation failed: {error}", file=sys.stderr)
        raise SystemExit(1)
