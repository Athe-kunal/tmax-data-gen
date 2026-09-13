"""Builds the Kùzu knowledge graph from the YAML artifact catalog.

Unlike a shape-sniffing ingester, this module knows the catalog's schema up
front (see `data_gen.catalog`, which mirrors artifacts/schemas/*.yaml) and
builds a fixed, typed graph from it:

    (:Domain)-[:HAS_SKILL_TYPE]->(:SkillType)-[:HAS_PRIMITIVE]->(:Primitive)
    (:Domain)-[:HAS_PERSONA]->(:Persona)
    (:Language)-[:COMPATIBLE_WITH]->(:Domain)

`SkillType` and `Persona` ids are only unique within their owning domain (the
same skill-type id, e.g. "systems", recurs across several domains as a
distinct node), so their primary keys are scoped as "<domain_id>::<id>".
`Primitive` ids are unique catalog-wide today, but are scoped the same way
for the same reason - nothing here assumes that stays true.

Usage:
    uv run python -m data_gen.kg_builder \
        --artifacts-dir tmax-data-gen/artifacts \
        --db-path tmax-data-gen/data_gen/kg.db
"""

from __future__ import annotations

import logging
from pathlib import Path

import kuzu

from data_gen.catalog import Catalog, DomainBundle, Language, load_catalog

logger = logging.getLogger(__name__)


def _create_schema(conn: kuzu.Connection) -> None:
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Domain("
        "id STRING, name STRING, description STRING, tags STRING[], "
        "PRIMARY KEY(id))"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS SkillType("
        "key STRING, domain_id STRING, id STRING, name STRING, "
        "PRIMARY KEY(key))"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Primitive("
        "key STRING, domain_id STRING, id STRING, description STRING, "
        "goal STRING, expected_operations STRING[], constraints STRING[], "
        "likely_tools STRING[], "
        "PRIMARY KEY(key))"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Persona("
        "key STRING, domain_id STRING, id STRING, role STRING, description STRING, "
        "PRIMARY KEY(key))"
    )
    conn.execute(
        "CREATE NODE TABLE IF NOT EXISTS Language("
        "id STRING, name STRING, sampling_weight DOUBLE, runtime STRING, "
        "package_manager STRING, build_command STRING, test_command STRING, "
        "base_image STRING, "
        "PRIMARY KEY(id))"
    )
    conn.execute("CREATE REL TABLE IF NOT EXISTS HAS_SKILL_TYPE(FROM Domain TO SkillType)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS HAS_PRIMITIVE(FROM SkillType TO Primitive)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS HAS_PERSONA(FROM Domain TO Persona)")
    conn.execute("CREATE REL TABLE IF NOT EXISTS COMPATIBLE_WITH(FROM Language TO Domain)")


def _ingest_domain_bundle(conn: kuzu.Connection, bundle: DomainBundle) -> None:
    domain = bundle.domain
    conn.execute(
        "MERGE (d:Domain {id: $id}) SET d.name = $name, d.description = $description, d.tags = $tags",
        {"id": domain.id, "name": domain.name, "description": domain.description, "tags": domain.tags},
    )

    for skill_type in bundle.skills.skill_types:
        skill_type_key = f"{domain.id}::{skill_type.id}"
        conn.execute(
            "MERGE (s:SkillType {key: $key}) SET s.domain_id = $domain_id, s.id = $id, s.name = $name",
            {"key": skill_type_key, "domain_id": domain.id, "id": skill_type.id, "name": skill_type.name},
        )
        conn.execute(
            """
            MATCH (d:Domain {id: $domain_id}), (s:SkillType {key: $key})
            MERGE (d)-[:HAS_SKILL_TYPE]->(s)
            """,
            {"domain_id": domain.id, "key": skill_type_key},
        )

        for primitive in skill_type.primitives:
            primitive_key = f"{domain.id}::{primitive.id}"
            guidance = primitive.guidance
            conn.execute(
                """
                MERGE (p:Primitive {key: $key})
                SET p.domain_id = $domain_id, p.id = $id, p.description = $description,
                    p.goal = $goal, p.expected_operations = $expected_operations,
                    p.constraints = $constraints, p.likely_tools = $likely_tools
                """,
                {
                    "key": primitive_key,
                    "domain_id": domain.id,
                    "id": primitive.id,
                    "description": primitive.description,
                    "goal": guidance.goal if guidance else None,
                    "expected_operations": guidance.expected_operations if guidance else [],
                    "constraints": guidance.constraints if guidance else [],
                    "likely_tools": guidance.likely_tools if guidance else [],
                },
            )
            conn.execute(
                """
                MATCH (s:SkillType {key: $skill_type_key}), (p:Primitive {key: $key})
                MERGE (s)-[:HAS_PRIMITIVE]->(p)
                """,
                {"skill_type_key": skill_type_key, "key": primitive_key},
            )

    for persona in bundle.personas.personas:
        persona_key = f"{domain.id}::{persona.id}"
        conn.execute(
            """
            MERGE (p:Persona {key: $key})
            SET p.domain_id = $domain_id, p.id = $id, p.role = $role, p.description = $description
            """,
            {
                "key": persona_key,
                "domain_id": domain.id,
                "id": persona.id,
                "role": persona.role,
                "description": persona.description,
            },
        )
        conn.execute(
            """
            MATCH (d:Domain {id: $domain_id}), (p:Persona {key: $key})
            MERGE (d)-[:HAS_PERSONA]->(p)
            """,
            {"domain_id": domain.id, "key": persona_key},
        )


def _ingest_language(conn: kuzu.Connection, language: Language) -> None:
    conn.execute(
        """
        MERGE (l:Language {id: $id})
        SET l.name = $name, l.sampling_weight = $sampling_weight, l.runtime = $runtime,
            l.package_manager = $package_manager, l.build_command = $build_command,
            l.test_command = $test_command, l.base_image = $base_image
        """,
        {
            "id": language.id,
            "name": language.name,
            "sampling_weight": language.sampling_weight,
            "runtime": language.runtime,
            "package_manager": language.package_manager,
            "build_command": language.build_command,
            "test_command": language.test_command,
            "base_image": language.base_image,
        },
    )
    for domain_id in language.compatible_domain_ids:
        conn.execute(
            """
            MATCH (l:Language {id: $language_id}), (d:Domain {id: $domain_id})
            MERGE (l)-[:COMPATIBLE_WITH]->(d)
            """,
            {"language_id": language.id, "domain_id": domain_id},
        )


def _ingest_catalog(conn: kuzu.Connection, catalog: Catalog) -> None:
    for bundle in catalog.domains:
        _ingest_domain_bundle(conn, bundle)
    for language in catalog.languages:
        _ingest_language(conn, language)


def build_graph(artifacts_dir: Path, db_path: Path) -> None:
    """Builds (or updates) the Kùzu knowledge graph from the YAML catalog.

    Safe to re-run: node/edge creation uses MERGE, so re-running against the
    same artifacts/ folder is idempotent.

    Args:
        artifacts_dir: Path to the tmax-data-gen/artifacts/ folder.
        db_path: Path to the on-disk Kùzu database directory (created if it
            doesn't exist).
    """
    catalog = load_catalog(artifacts_dir)

    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    try:
        _create_schema(conn)
        _ingest_catalog(conn, catalog)
    finally:
        conn.close()
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts-dir", type=Path, default=Path("tmax-data-gen/artifacts"))
    parser.add_argument("--db-path", type=Path, default=Path("tmax-data-gen/data_gen/kg.db"))
    args = parser.parse_args()

    build_graph(args.artifacts_dir, args.db_path)
    print(f"Knowledge graph built at {args.db_path}")
