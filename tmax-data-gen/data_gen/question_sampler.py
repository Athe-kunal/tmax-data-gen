"""Samples one catalog entry to seed the next generated question.

Picks a Domain -> SkillType -> Primitive path and a Persona uniformly at
random from that domain, and a Language weighted by its `sampling_weight`
(mirrors the language-axis weighting tmax's legacy task generator used, and
matches the sum-to-1.0 invariant `scripts/validate_catalog.py` enforces).
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path

from data_gen.catalog import Catalog, Domain, DomainBundle, Language, Persona, Primitive, SkillType
from data_gen.embeddings import EmbeddingClient
from data_gen.kg_retrieve import Match, retrieve
from data_gen.weave_logger import weave_op


@dataclass(frozen=True)
class SampledEntry:
    """One (domain, skill type, primitive, persona, language) sample."""

    domain: Domain
    skill_type: SkillType
    primitive: Primitive
    persona: Persona
    language: Language


def sample_entry(catalog: Catalog, rng: random.Random | None = None) -> SampledEntry:
    """Draws one SampledEntry from `catalog`.

    Args:
        catalog: The loaded artifact catalog (see `data_gen.catalog.load_catalog`).
        rng: Source of randomness; defaults to a fresh `random.Random()`.

    Returns:
        A SampledEntry ready to seed question generation.
    """
    rng = rng or random.Random()

    bundle = rng.choice(catalog.domains)
    skill_type = rng.choice(bundle.skills.skill_types)
    primitive = rng.choice(skill_type.primitives)
    persona = rng.choice(bundle.personas.personas)
    language = rng.choices(
        catalog.languages, weights=[language.sampling_weight for language in catalog.languages]
    )[0]

    return SampledEntry(
        domain=bundle.domain,
        skill_type=skill_type,
        primitive=primitive,
        persona=persona,
        language=language,
    )


@dataclass(frozen=True)
class RetrievedSample:
    """The result of retrieval-driven sampling: the entry plus provenance."""

    entry: SampledEntry
    query: str
    matches: list[Match]


def _find_bundle(catalog: Catalog, domain_id: str) -> DomainBundle:
    for bundle in catalog.domains:
        if bundle.domain.id == domain_id:
            return bundle
    raise ValueError(f"Unknown domain id {domain_id!r} in catalog")


def _find_primitive(bundle: DomainBundle, primitive_id: str) -> tuple[SkillType, Primitive]:
    for skill_type in bundle.skills.skill_types:
        for primitive in skill_type.primitives:
            if primitive.id == primitive_id:
                return skill_type, primitive
    raise ValueError(f"Unknown primitive id {primitive_id!r} in domain {bundle.domain.id!r}")


def _find_persona(bundle: DomainBundle, persona_id: str) -> Persona:
    for persona in bundle.personas.personas:
        if persona.id == persona_id:
            return persona
    raise ValueError(f"Unknown persona id {persona_id!r} in domain {bundle.domain.id!r}")


@weave_op
def sample_entry_via_retrieval(
    catalog: Catalog,
    query: str,
    kg_db_path: Path,
    embedding_client: EmbeddingClient | None = None,
    top_k: int = 5,
    rng: random.Random | None = None,
) -> RetrievedSample:
    """Retrieves the KG node most relevant to `query` and resolves it to a SampledEntry.

    The matched node determines part of the sample (a Primitive match fixes
    domain+skill_type+primitive; a Persona match fixes domain+persona; a
    Domain match fixes only the domain) - anything the match doesn't
    determine is filled in by uniform/weighted random sampling, same as
    `sample_entry`.

    Decorated with `@weave_op` so the query and every retrieved triplet are
    traced to Weave, alongside the `generate_question` call it feeds.

    Args:
        catalog: The loaded artifact catalog.
        query: Natural-language retrieval query.
        kg_db_path: Path to the Kùzu database built by `kg_builder`.
        embedding_client: Client to embed `query` and the KG's nodes with;
            defaults to one configured from the EMBEDDING_* env vars.
        top_k: How many candidate nodes `kg_retrieve.retrieve` considers;
            only the top match is used to seed the sample.
        rng: Source of randomness for the parts the match doesn't fix.

    Returns:
        A RetrievedSample with the resolved entry and full retrieval provenance.
    """
    rng = rng or random.Random()
    matches = retrieve(query, kg_db_path, client=embedding_client, top_k=top_k)
    if not matches:
        raise ValueError(f"No KG matches found for query {query!r}")

    top = matches[0]
    node_type, key = top.node_id.split("::", 1)

    if node_type == "Primitive":
        domain_id, primitive_id = key.split("::", 1)
        bundle = _find_bundle(catalog, domain_id)
        skill_type, primitive = _find_primitive(bundle, primitive_id)
        persona = rng.choice(bundle.personas.personas)
    elif node_type == "Persona":
        domain_id, persona_id = key.split("::", 1)
        bundle = _find_bundle(catalog, domain_id)
        persona = _find_persona(bundle, persona_id)
        skill_type = rng.choice(bundle.skills.skill_types)
        primitive = rng.choice(skill_type.primitives)
    elif node_type == "Domain":
        bundle = _find_bundle(catalog, key)
        skill_type = rng.choice(bundle.skills.skill_types)
        primitive = rng.choice(skill_type.primitives)
        persona = rng.choice(bundle.personas.personas)
    else:
        raise ValueError(f"Unexpected matched node type {node_type!r} for node id {top.node_id!r}")

    language = rng.choices(
        catalog.languages, weights=[language.sampling_weight for language in catalog.languages]
    )[0]

    entry = SampledEntry(
        domain=bundle.domain, skill_type=skill_type, primitive=primitive, persona=persona, language=language
    )
    return RetrievedSample(entry=entry, query=query, matches=matches)
