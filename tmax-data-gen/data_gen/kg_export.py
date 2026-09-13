"""Exports the full Kùzu knowledge graph to a plain JSON {nodes, edges} blob.

Fully schema-agnostic: table names, columns, and primary keys are all
discovered via Kùzu's own introspection (SHOW_TABLES / TABLE_INFO /
SHOW_CONNECTION), so this works regardless of what axes/shapes kg_builder
produced.

Usage:
    uv run python -m data_gen.kg_export \
        --db-path tmax-data-gen/data_gen/kg.db \
        --out tmax-data-gen/data_gen/kg_export.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import kuzu


def _table_names(conn: kuzu.Connection, table_type: str) -> list[str]:
    return [row[1] for row in conn.execute("CALL SHOW_TABLES() RETURN *") if row[2] == table_type]


def _columns(conn: kuzu.Connection, table: str) -> list[str]:
    return [row[1] for row in conn.execute(f"CALL TABLE_INFO('{table}') RETURN *")]


def _primary_key_column(conn: kuzu.Connection, table: str) -> str:
    for row in conn.execute(f"CALL TABLE_INFO('{table}') RETURN *"):
        _, name, _, _, is_primary_key = row
        if is_primary_key:
            return name
    raise ValueError(f"No primary key found for node table {table!r}")


def export_graph(db_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Reads every node/rel table in the Kùzu DB at `db_path` into JSON.

    Returns:
        {"nodes": [{"id", "type", "properties": {...}}, ...],
         "edges": [{"source", "target", "type"}, ...]}
        where node "id" is "<table>::<primary_key_value>", stable across
        exports as long as the underlying data doesn't change.
    """
    db = kuzu.Database(str(db_path), read_only=True)
    conn = kuzu.Connection(db)
    try:
        nodes: list[dict[str, Any]] = []
        for table in _table_names(conn, "NODE"):
            columns = _columns(conn, table)
            pk = _primary_key_column(conn, table)
            select = ", ".join(f"n.{col}" for col in columns)
            for row in conn.execute(f"MATCH (n:{table}) RETURN {select}"):
                properties = dict(zip(columns, row))
                nodes.append(
                    {
                        "id": f"{table}::{properties[pk]}",
                        "type": table,
                        "properties": properties,
                    }
                )

        edges: list[dict[str, Any]] = []
        for rel_table in _table_names(conn, "REL"):
            for src_table, dst_table, src_pk, dst_pk in conn.execute(
                f"CALL SHOW_CONNECTION('{rel_table}') RETURN *"
            ):
                for src_val, dst_val in conn.execute(
                    f"MATCH (a:{src_table})-[:{rel_table}]->(b:{dst_table}) "
                    f"RETURN a.{src_pk}, b.{dst_pk}"
                ):
                    edges.append(
                        {
                            "source": f"{src_table}::{src_val}",
                            "target": f"{dst_table}::{dst_val}",
                            "type": rel_table,
                        }
                    )

        return {"nodes": nodes, "edges": edges}
    finally:
        conn.close()
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=Path("tmax-data-gen/data_gen/kg.db"))
    parser.add_argument("--out", type=Path, default=Path("tmax-data-gen/data_gen/kg_export.json"))
    args = parser.parse_args()

    graph = export_graph(args.db_path)
    args.out.write_text(json.dumps(graph, indent=2))
    print(f"Exported {len(graph['nodes'])} nodes, {len(graph['edges'])} edges to {args.out}")
