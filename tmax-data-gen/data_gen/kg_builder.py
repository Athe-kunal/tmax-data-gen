"""Builds the Kùzu knowledge graph from the artifacts/ folder, generically.

Nothing in this module is keyed by axis/folder *name*. Instead, each
artifacts/<axis>/<axis>.json is classified by its JSON *shape* (see
`_classify_shape`), and each shape maps to a generic ingestion strategy.
Renaming a folder, or adding a brand-new axis whose JSON matches one of the
shapes below, works with zero code changes here.

Recognized shapes:
    flat_list          ["a", "b", ...]
                        -> one standalone node per string, keyed by value.
    list_of_dicts       [{"k1": v1, "k2": v2}, ...]
                        -> one standalone node per dict, columns = union of
                           dict keys (types inferred from the values).
    dict_of_list        {"key1": ["a", "b"], "key2": [...]}
                        -> top-level keys resolve to an existing parent node
                           type (see below) or a new one; list entries become
                           leaf nodes (deduped globally by value), linked
                           parent -[:HAS_<AXIS>]-> leaf.
    nested_dict_of_list {"key1": {"g1": ["a", "b"]}, ...}
                        -> parent (as above) -> group (scoped as
                           "<key>::<group>", never deduped across different
                           keys - see module docstring) -> leaf (deduped
                           globally by value).
    dict_of_scalar      {"key1": "text", "key2": "text"}
                        -> sets a property (named after the axis) on the
                           matched parent node.
    kinds_fragments     {"kinds": [...], "prompt_fragments": {...}}
                        -> one standalone node per `kinds` entry, with the
                           matching fragment (or "") as a property.

Parent-node resolution for dict-keyed shapes: the top-level keys are matched
by *value* against every already-built `flat_list` node table (e.g. if
`domain.json` produced a table whose values are exactly the 9 domain names,
any other axis whose dict keys are also exactly those 9 strings reuses that
same table/nodes automatically - no hardcoded "Domain" concept anywhere).
If no existing flat_list table's values are a superset of an axis's keys, a
new parent table is created and named after that axis.

Redundant axes are detected structurally, not by name: if a `dict_of_list`
axis's per-key value sets exactly match the per-key group-key sets of some
`nested_dict_of_list` axis, it's a duplicate view of that axis's grouping
level (e.g. a "skill_type.json" that's just the keys of a
"primitive_skills.json") and is skipped.

This module only builds the *structural* graph implied by the source JSON.
It intentionally does not add cross-axis compatibility edges (e.g.
language <-> skill) - those are decided dynamically by the Question Agent
at generation time, not baked into the graph ahead of time.

Usage:
    uv run python -m data_gen.kg_builder \
        --artifacts-dir tmax-data-gen/artifacts \
        --db-path tmax-data-gen/data_gen/kg.db
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import kuzu

logger = logging.getLogger(__name__)

Shape = Literal[
    "flat_list",
    "list_of_dicts",
    "dict_of_list",
    "nested_dict_of_list",
    "dict_of_scalar",
    "kinds_fragments",
]


def _classify_shape(data: object) -> Shape | None:
    """Classifies the structural shape of a loaded axis JSON value."""
    if isinstance(data, list) and data:
        if all(isinstance(x, str) for x in data):
            return "flat_list"
        if all(isinstance(x, dict) for x in data):
            return "list_of_dicts"
        return None

    if isinstance(data, dict) and data:
        if set(data.keys()) == {"kinds", "prompt_fragments"}:
            return "kinds_fragments"

        values = list(data.values())
        if all(isinstance(v, str) for v in values):
            return "dict_of_scalar"
        if all(isinstance(v, list) and all(isinstance(x, str) for x in v) for v in values):
            return "dict_of_list"
        if all(isinstance(v, dict) for v in values):
            inner_values = [iv for v in values for iv in v.values()]
            if inner_values and all(
                isinstance(iv, list) and all(isinstance(x, str) for x in iv) for iv in inner_values
            ):
                return "nested_dict_of_list"
    return None


def _pascal_case(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_"))


def _label_before_parenthetical(value: str) -> str:
    """Returns the human-readable prefix of a "<label> (<details>)" string."""
    return value.split(" (", 1)[0].strip()


def _kuzu_type(value: object) -> str:
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INT64"
    if isinstance(value, float):
        return "DOUBLE"
    return "STRING"


@dataclass
class _ParentRegistry:
    """Tracks flat_list node tables so dict-keyed axes can be linked to them.

    table_values maps table_name -> the set of string values (== primary
    keys) it contains, so later axes can find a table whose values are a
    superset of their own top-level keys.
    """

    table_values: dict[str, set[str]] = field(default_factory=dict)
    # axis_name -> {outer_key: set(group_keys)}, used to detect dict_of_list
    # axes that are redundant with a nested_dict_of_list axis's grouping level.
    nested_group_keys: dict[str, dict[str, set[str]]] = field(default_factory=dict)

    def resolve_parent_table(self, keys: set[str], conn: kuzu.Connection, axis_name: str) -> str:
        """Returns a table name whose known values are a superset of `keys`.

        Falls back to creating a new standalone table (named after the axis
        whose keys couldn't be matched) if nothing existing qualifies.
        """
        candidates = sorted(
            table for table, values in self.table_values.items() if keys <= values
        )
        if candidates:
            if len(candidates) > 1:
                logger.warning(
                    "Multiple existing node tables (%s) match axis %r's keys; using %r",
                    candidates, axis_name, candidates[0],
                )
            return candidates[0]

        table = _pascal_case(axis_name) + "Key"
        conn.execute(f"CREATE NODE TABLE IF NOT EXISTS {table}(value STRING, PRIMARY KEY(value))")
        for key in keys:
            conn.execute(f"MERGE (n:{table} {{value: $value}})", {"value": key})
        self.table_values[table] = set(keys)
        return table


def _load_json(axis_dir: Path) -> object:
    return json.loads((axis_dir / f"{axis_dir.name}.json").read_text())


def _ingest_flat_list(conn: kuzu.Connection, axis_name: str, data: list[str], registry: _ParentRegistry) -> None:
    table = _pascal_case(axis_name)
    conn.execute(
        f"CREATE NODE TABLE IF NOT EXISTS {table}(value STRING, label STRING, PRIMARY KEY(value))"
    )
    for value in data:
        conn.execute(
            f"MERGE (n:{table} {{value: $value}}) SET n.label = $label",
            {"value": value, "label": _label_before_parenthetical(value)},
        )
    registry.table_values[table] = set(data)


def _ingest_list_of_dicts(conn: kuzu.Connection, axis_name: str, data: list[dict]) -> None:
    table = _pascal_case(axis_name)
    columns = {}
    for row in data:
        for key, value in row.items():
            columns.setdefault(key, _kuzu_type(value))
    column_defs = ", ".join(f"{key} {kuzu_type}" for key, kuzu_type in columns.items())
    conn.execute(f"CREATE NODE TABLE IF NOT EXISTS {table}(id INT64, {column_defs}, PRIMARY KEY(id))")
    for idx, row in enumerate(data):
        params = {"id": idx, **{key: row.get(key) for key in columns}}
        assignments = ", ".join(f"n.{key} = ${key}" for key in columns)
        conn.execute(f"MERGE (n:{table} {{id: $id}}) SET {assignments}", params)


def _ingest_dict_of_list(
    conn: kuzu.Connection, axis_name: str, data: dict[str, list[str]], registry: _ParentRegistry
) -> None:
    for nested_axis, group_keys in registry.nested_group_keys.items():
        if group_keys.keys() >= data.keys() and all(
            set(values) == group_keys.get(key, set()) for key, values in data.items()
        ):
            logger.info("Skipping axis %r: redundant with %r's grouping level", axis_name, nested_axis)
            return

    parent_table = registry.resolve_parent_table(set(data.keys()), conn, axis_name)
    leaf_table = _pascal_case(axis_name)
    rel_name = f"HAS_{axis_name.upper()}"
    conn.execute(f"CREATE NODE TABLE IF NOT EXISTS {leaf_table}(value STRING, PRIMARY KEY(value))")
    conn.execute(f"CREATE REL TABLE IF NOT EXISTS {rel_name}(FROM {parent_table} TO {leaf_table})")

    for parent_value, leaves in data.items():
        conn.execute(f"MERGE (p:{parent_table} {{value: $value}})", {"value": parent_value})
        for leaf in leaves:
            conn.execute(f"MERGE (l:{leaf_table} {{value: $value}})", {"value": leaf})
            conn.execute(
                f"""
                MATCH (p:{parent_table} {{value: $parent_value}}), (l:{leaf_table} {{value: $leaf}})
                MERGE (p)-[:{rel_name}]->(l)
                """,
                {"parent_value": parent_value, "leaf": leaf},
            )


def _ingest_nested_dict_of_list(
    conn: kuzu.Connection, axis_name: str, data: dict[str, dict[str, list[str]]], registry: _ParentRegistry
) -> None:
    parent_table = registry.resolve_parent_table(set(data.keys()), conn, axis_name)
    group_table = _pascal_case(axis_name) + "Group"
    leaf_table = _pascal_case(axis_name)
    parent_to_group_rel = f"HAS_{axis_name.upper()}_GROUP"
    group_to_leaf_rel = f"HAS_{axis_name.upper()}"

    conn.execute(f"CREATE NODE TABLE IF NOT EXISTS {group_table}(id STRING, name STRING, PRIMARY KEY(id))")
    conn.execute(f"CREATE NODE TABLE IF NOT EXISTS {leaf_table}(value STRING, PRIMARY KEY(value))")
    conn.execute(f"CREATE REL TABLE IF NOT EXISTS {parent_to_group_rel}(FROM {parent_table} TO {group_table})")
    conn.execute(f"CREATE REL TABLE IF NOT EXISTS {group_to_leaf_rel}(FROM {group_table} TO {leaf_table})")

    registry.nested_group_keys[axis_name] = {}
    for parent_value, groups in data.items():
        conn.execute(f"MERGE (p:{parent_table} {{value: $value}})", {"value": parent_value})
        registry.nested_group_keys[axis_name][parent_value] = set(groups.keys())
        for group_name, leaves in groups.items():
            # Scoped as parent::group, never deduped by group_name alone - see
            # module docstring (e.g. "Algorithmic" under two different parent
            # values must not collapse into one shared bucket of leaves).
            group_id = f"{parent_value}::{group_name}"
            conn.execute(
                f"MERGE (g:{group_table} {{id: $id}}) SET g.name = $name",
                {"id": group_id, "name": group_name},
            )
            conn.execute(
                f"""
                MATCH (p:{parent_table} {{value: $parent_value}}), (g:{group_table} {{id: $group_id}})
                MERGE (p)-[:{parent_to_group_rel}]->(g)
                """,
                {"parent_value": parent_value, "group_id": group_id},
            )
            for leaf in leaves:
                conn.execute(f"MERGE (l:{leaf_table} {{value: $value}})", {"value": leaf})
                conn.execute(
                    f"""
                    MATCH (g:{group_table} {{id: $group_id}}), (l:{leaf_table} {{value: $leaf}})
                    MERGE (g)-[:{group_to_leaf_rel}]->(l)
                    """,
                    {"group_id": group_id, "leaf": leaf},
                )


def _ingest_dict_of_scalar(
    conn: kuzu.Connection, axis_name: str, data: dict[str, str], registry: _ParentRegistry
) -> None:
    parent_table = registry.resolve_parent_table(set(data.keys()), conn, axis_name)
    conn.execute(f"ALTER TABLE {parent_table} ADD IF NOT EXISTS {axis_name} STRING")
    for key, value in data.items():
        conn.execute(
            f"MATCH (p:{parent_table} {{value: $key}}) SET p.{axis_name} = $value",
            {"key": key, "value": value},
        )


def _ingest_kinds_fragments(conn: kuzu.Connection, axis_name: str, data: dict[str, object]) -> None:
    table = _pascal_case(axis_name)
    fragments: dict[str, str] = data["prompt_fragments"]
    conn.execute(
        f"CREATE NODE TABLE IF NOT EXISTS {table}(value STRING, prompt_fragment STRING, PRIMARY KEY(value))"
    )
    for kind in data["kinds"]:
        conn.execute(
            f"MERGE (n:{table} {{value: $value}}) SET n.prompt_fragment = $fragment",
            {"value": kind, "fragment": fragments.get(kind, "")},
        )


def build_graph(artifacts_dir: Path, db_path: Path) -> None:
    """Builds (or updates) the Kùzu knowledge graph from artifacts/ JSON files.

    Axes are discovered by listing `artifacts_dir` and classified by JSON
    shape (see module docstring) - nothing here is keyed by folder name, so
    renaming folders or adding new axes with a recognized shape works
    without code changes. Any folder whose JSON doesn't match a known shape
    is skipped with a warning.

    Processing is ordered by shape (flat_list and nested_dict_of_list first)
    so that dict-keyed axes can resolve their parent node type by matching
    values against tables already built, regardless of directory iteration
    order.

    Safe to re-run: node/edge creation uses MERGE, so re-running against the
    same artifacts/ folder is idempotent.

    Args:
        artifacts_dir: Path to the tmax-data-gen/artifacts/ folder.
        db_path: Path to the on-disk Kùzu database directory (created if it
            doesn't exist).
    """
    axis_data: dict[str, object] = {}
    for axis_dir in sorted(p for p in artifacts_dir.iterdir() if p.is_dir()):
        axis_data[axis_dir.name] = _load_json(axis_dir)

    shapes = {name: _classify_shape(data) for name, data in axis_data.items()}
    for name, shape in shapes.items():
        if shape is None:
            logger.warning("Could not classify shape of artifacts axis %r, skipping", name)

    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    registry = _ParentRegistry()
    try:
        # Order matters: flat_list tables and nested_dict_of_list group-key
        # sets must exist before dict_of_list/dict_of_scalar axes try to
        # resolve a parent table or check for redundancy against them.
        order: list[Shape] = [
            "flat_list", "nested_dict_of_list", "dict_of_list", "dict_of_scalar", "list_of_dicts", "kinds_fragments",
        ]
        for shape in order:
            for name, data in axis_data.items():
                if shapes[name] != shape:
                    continue
                if shape == "flat_list":
                    _ingest_flat_list(conn, name, data, registry)
                elif shape == "list_of_dicts":
                    _ingest_list_of_dicts(conn, name, data)
                elif shape == "dict_of_list":
                    _ingest_dict_of_list(conn, name, data, registry)
                elif shape == "nested_dict_of_list":
                    _ingest_nested_dict_of_list(conn, name, data, registry)
                elif shape == "dict_of_scalar":
                    _ingest_dict_of_scalar(conn, name, data, registry)
                elif shape == "kinds_fragments":
                    _ingest_kinds_fragments(conn, name, data)
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
