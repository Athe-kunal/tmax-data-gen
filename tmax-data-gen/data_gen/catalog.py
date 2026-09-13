"""Dataclasses for the tharun-style YAML artifact catalog.

Mirrors artifacts/schemas/*.yaml exactly:
    index.schema.yaml    -> CatalogIndex, DomainIndexEntry, LanguageIndexEntry
    domain.schema.yaml   -> Domain
    skill.schema.yaml    -> SkillCatalog, SkillType, Primitive, PrimitiveGuidance
    persona.schema.yaml  -> PersonaCatalog, Persona
    language.schema.yaml -> Language

`load_catalog` is the single entry point: it reads artifacts/index.yaml and,
for every file it references, dispatches to the parser registered for that
file's owning folder (see `_FOLDER_PARSERS`), so adding a new domain or
language YAML file requires no code change here - only an index.yaml entry.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

import yaml


@dataclass(frozen=True)
class PrimitiveGuidance:
    """Optional authored enrichment on a primitive skill."""

    origin: str
    goal: str
    expected_operations: list[str]
    constraints: list[str] = field(default_factory=list)
    likely_tools: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PrimitiveGuidance":
        return PrimitiveGuidance(
            origin=data["origin"],
            goal=data["goal"],
            expected_operations=list(data["expected_operations"]),
            constraints=list(data.get("constraints", [])),
            likely_tools=list(data.get("likely_tools", [])),
        )


@dataclass(frozen=True)
class Primitive:
    """A single primitive skill within a skill type."""

    id: str
    description: str
    guidance: PrimitiveGuidance | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Primitive":
        guidance = data.get("guidance")
        return Primitive(
            id=data["id"],
            description=data["description"],
            guidance=PrimitiveGuidance.from_dict(guidance) if guidance else None,
        )


@dataclass(frozen=True)
class SkillType:
    """A named grouping of primitive skills within a domain."""

    id: str
    name: str
    primitives: list[Primitive]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SkillType":
        return SkillType(
            id=data["id"],
            name=data["name"],
            primitives=[Primitive.from_dict(p) for p in data["primitives"]],
        )


@dataclass(frozen=True)
class SkillCatalog:
    """The full skill taxonomy for one domain (artifacts/skills/<domain>.yaml)."""

    schema_version: int
    domain_id: str
    skill_types: list[SkillType]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "SkillCatalog":
        return SkillCatalog(
            schema_version=data["schema_version"],
            domain_id=data["domain_id"],
            skill_types=[SkillType.from_dict(st) for st in data["skill_types"]],
        )


@dataclass(frozen=True)
class Persona:
    """A single task-framing persona."""

    id: str
    role: str
    description: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Persona":
        return Persona(id=data["id"], role=data["role"], description=data["description"])


@dataclass(frozen=True)
class PersonaCatalog:
    """All personas for one domain (artifacts/personas/<domain>.yaml)."""

    schema_version: int
    domain_id: str
    personas: list[Persona]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PersonaCatalog":
        return PersonaCatalog(
            schema_version=data["schema_version"],
            domain_id=data["domain_id"],
            personas=[Persona.from_dict(p) for p in data["personas"]],
        )


@dataclass(frozen=True)
class Domain:
    """One Tmax domain (artifacts/domains/<domain>.yaml)."""

    schema_version: int
    id: str
    name: str
    description: str
    tags: list[str] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Domain":
        return Domain(
            schema_version=data["schema_version"],
            id=data["id"],
            name=data["name"],
            description=data["description"],
            tags=list(data.get("tags", [])),
        )


@dataclass(frozen=True)
class Language:
    """One programming-language/runtime profile (artifacts/languages/<id>.yaml)."""

    schema_version: int
    id: str
    name: str
    sampling_weight: float
    runtime: str
    runtime_guidance_origin: str
    package_manager: str
    build_command: str
    test_command: str
    compatible_domain_ids: list[str] = field(default_factory=list)
    base_image: str | None = None

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Language":
        return Language(
            schema_version=data["schema_version"],
            id=data["id"],
            name=data["name"],
            sampling_weight=data["sampling_weight"],
            runtime=data["runtime"],
            runtime_guidance_origin=data["runtime_guidance_origin"],
            package_manager=data["package_manager"],
            build_command=data["build_command"],
            test_command=data["test_command"],
            compatible_domain_ids=list(data.get("compatible_domain_ids", [])),
            base_image=data.get("base_image"),
        )


@dataclass(frozen=True)
class DomainIndexEntry:
    id: str
    domain_file: str
    skill_file: str
    persona_file: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DomainIndexEntry":
        return DomainIndexEntry(
            id=data["id"],
            domain_file=data["domain_file"],
            skill_file=data["skill_file"],
            persona_file=data["persona_file"],
        )


@dataclass(frozen=True)
class LanguageIndexEntry:
    id: str
    file: str

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "LanguageIndexEntry":
        return LanguageIndexEntry(id=data["id"], file=data["file"])


@dataclass(frozen=True)
class CatalogIndex:
    """artifacts/index.yaml: the runtime entry point listing every file."""

    schema_version: int
    domains: list[DomainIndexEntry]
    languages: list[LanguageIndexEntry]

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "CatalogIndex":
        return CatalogIndex(
            schema_version=data["schema_version"],
            domains=[DomainIndexEntry.from_dict(d) for d in data["domains"]],
            languages=[LanguageIndexEntry.from_dict(l) for l in data["languages"]],
        )


@dataclass(frozen=True)
class DomainBundle:
    """A domain together with its skill taxonomy and personas."""

    domain: Domain
    skills: SkillCatalog
    personas: PersonaCatalog


@dataclass(frozen=True)
class Catalog:
    """The fully resolved artifact catalog, ready for graph construction."""

    domains: list[DomainBundle]
    languages: list[Language]


# Maps the top-level folder a YAML file lives in to the parser for that
# folder's schema. `load_catalog` derives the folder from each path index.yaml
# references, so registering a new folder here is the only change needed to
# support a new artifact kind.
_FOLDER_PARSERS: dict[str, Callable[[dict[str, Any]], Any]] = {
    "domains": Domain.from_dict,
    "skills": SkillCatalog.from_dict,
    "personas": PersonaCatalog.from_dict,
    "languages": Language.from_dict,
}


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text())


def _parse_by_folder(artifacts_dir: Path, relative_path: str) -> Any:
    folder_name = relative_path.split("/", 1)[0]
    parser = _FOLDER_PARSERS.get(folder_name)
    if parser is None:
        raise ValueError(
            f"No parser registered for folder {folder_name!r} (from {relative_path!r}); "
            f"known folders: {sorted(_FOLDER_PARSERS)}"
        )
    return parser(_load_yaml(artifacts_dir / relative_path))


def load_catalog(artifacts_dir: Path) -> Catalog:
    """Loads the full artifact catalog rooted at `artifacts_dir/index.yaml`.

    Every file path is read from the index and parsed into the dataclass
    registered for its containing folder (see `_FOLDER_PARSERS`) - nothing
    here is keyed by domain or language name.

    Args:
        artifacts_dir: Path to the tmax-data-gen/artifacts/ folder.

    Returns:
        The resolved Catalog.
    """
    index = CatalogIndex.from_dict(_load_yaml(artifacts_dir / "index.yaml"))

    bundles = []
    for entry in index.domains:
        domain = _parse_by_folder(artifacts_dir, entry.domain_file)
        skills = _parse_by_folder(artifacts_dir, entry.skill_file)
        personas = _parse_by_folder(artifacts_dir, entry.persona_file)
        bundles.append(DomainBundle(domain=domain, skills=skills, personas=personas))

    languages = [_parse_by_folder(artifacts_dir, entry.file) for entry in index.languages]

    return Catalog(domains=bundles, languages=languages)
