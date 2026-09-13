"""Natural-language -> knowledge-graph triplet retrieval.

Embeds every content-bearing node (Domain, Primitive, Persona - the node
types that carry free-text descriptions; SkillType and Language are short
labels retrieved as context around a match, not embedded themselves) via
`EmbeddingClient`. A query is embedded with the same client, matched against
those node embeddings by cosine similarity, and the direct graph triplets
touching each matched node are returned.

Embeddings are cached to `<db_path>.embeddings.json`, keyed by node id and
tagged with the embedding model name, so unchanged catalogs don't re-embed
on every call.

Usage:
    uv run python -m data_gen.kg_retrieve --db-path data_gen/kg.db \
        "how do I harden SSH keys"
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import kuzu

from data_gen.embeddings import EmbeddingClient

# Node types with free text worth embedding directly.
_EMBEDDABLE_NODE_TYPES = ("Domain", "Primitive", "Persona")


@dataclass(frozen=True)
class Triplet:
    """A single (subject, relation, object) edge, with human-readable labels."""

    subject_type: str
    subject_label: str
    relation: str
    object_type: str
    object_label: str

    def __str__(self) -> str:
        return (
            f"({self.subject_type} '{self.subject_label}') "
            f"-[{self.relation}]-> "
            f"({self.object_type} '{self.object_label}')"
        )


@dataclass(frozen=True)
class Match:
    """One retrieved node and the triplets anchored at it."""

    node_type: str
    node_id: str
    similarity: float
    triplets: list[Triplet]


def _node_text(node_type: str, properties: dict) -> str:
    if node_type == "Domain":
        return f"{properties['name']}: {properties['description']}"
    if node_type == "Primitive":
        return f"{properties['description']}. Goal: {properties.get('goal') or ''}"
    if node_type == "Persona":
        return f"{properties['role']}: {properties['description']}"
    raise ValueError(f"No text representation defined for node type {node_type!r}")


def _node_label(node_type: str, properties: dict) -> str:
    if node_type == "Domain":
        return properties["name"]
    if node_type == "Primitive":
        return properties["description"]
    if node_type == "Persona":
        return properties["role"]
    if node_type == "SkillType":
        return properties["name"]
    if node_type == "Language":
        return properties["name"]
    return properties.get("id") or properties.get("key") or ""


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    return dot / (norm_a * norm_b) if norm_a and norm_b else 0.0


def _fetch_embeddable_nodes(conn: kuzu.Connection) -> dict[str, dict[str, object]]:
    """Returns {node_id: {"type": ..., "properties": ..., "text": ...}}."""
    nodes: dict[str, dict[str, object]] = {}
    for node_type in _EMBEDDABLE_NODE_TYPES:
        pk_column = "key" if node_type in ("Primitive", "Persona") else "id"
        result = conn.execute(f"MATCH (n:{node_type}) RETURN n.*")
        columns = [c.split(".", 1)[1] for c in result.get_column_names()]
        for row in result:
            properties = dict(zip(columns, row))
            node_id = f"{node_type}::{properties[pk_column]}"
            nodes[node_id] = {
                "type": node_type,
                "properties": properties,
                "text": _node_text(node_type, properties),
            }
    return nodes


def _cache_path(db_path: Path) -> Path:
    return db_path.parent / f"{db_path.name}.embeddings.json"


def _load_cache(cache_path: Path, model: str, node_ids: set[str]) -> dict[str, list[float]] | None:
    if not cache_path.is_file():
        return None
    cached = json.loads(cache_path.read_text())
    if cached.get("model") != model or set(cached.get("vectors", {})) != node_ids:
        return None
    return cached["vectors"]


def _save_cache(cache_path: Path, model: str, vectors: dict[str, list[float]]) -> None:
    cache_path.write_text(json.dumps({"model": model, "vectors": vectors}))


def _embed_nodes(
    conn: kuzu.Connection, client: EmbeddingClient, db_path: Path
) -> tuple[dict[str, dict[str, object]], dict[str, list[float]]]:
    nodes = _fetch_embeddable_nodes(conn)
    cache_path = _cache_path(db_path)
    vectors = _load_cache(cache_path, client.model, set(nodes))
    if vectors is None:
        node_ids = list(nodes)
        texts = [nodes[node_id]["text"] for node_id in node_ids]
        embedded = client.embed(texts)
        vectors = dict(zip(node_ids, embedded))
        _save_cache(cache_path, client.model, vectors)
    return nodes, vectors


def _triplets_for_node(conn: kuzu.Connection, node_type: str, properties: dict) -> list[Triplet]:
    """Returns every triplet with an edge directly touching this node.

    `m.*` on an untyped match variable returns the union of every node
    table's columns (None-padded for columns the actual matched type
    doesn't have), so column names must come from this exact query's
    result - not from a separately re-typed query, whose column set and
    order would differ - or the zip below would misalign values.
    """
    pk_column = "key" if node_type in ("Primitive", "Persona", "SkillType") else "id"
    pk_value = properties[pk_column]

    triplets: list[Triplet] = []

    outgoing = conn.execute(
        f"MATCH (n:{node_type} {{{pk_column}: $value}})-[r]->(m) RETURN label(r), label(m), m.*",
        {"value": pk_value},
    )
    object_columns = [c.split(".", 1)[1] for c in outgoing.get_column_names()[2:]]
    for relation, object_type, *object_values in outgoing:
        object_properties = dict(zip(object_columns, object_values))
        triplets.append(
            Triplet(
                subject_type=node_type,
                subject_label=_node_label(node_type, properties),
                relation=relation,
                object_type=object_type,
                object_label=_node_label(object_type, object_properties),
            )
        )

    incoming = conn.execute(
        f"MATCH (m)-[r]->(n:{node_type} {{{pk_column}: $value}}) RETURN label(m), m.*, label(r)",
        {"value": pk_value},
    )
    subject_columns = [c.split(".", 1)[1] for c in incoming.get_column_names()[1:-1]]
    for row in incoming:
        subject_type, relation = row[0], row[-1]
        subject_properties = dict(zip(subject_columns, row[1:-1]))
        triplets.append(
            Triplet(
                subject_type=subject_type,
                subject_label=_node_label(subject_type, subject_properties),
                relation=relation,
                object_type=node_type,
                object_label=_node_label(node_type, properties),
            )
        )

    return triplets


def build_embeddings_cache(db_path: Path, client: EmbeddingClient | None = None) -> int:
    """Builds (or refreshes, if the catalog changed) the node embeddings
    cache at `<db_path>.embeddings.json`, without running any query.

    Every `retrieve()` call already does this as a side effect via
    `_embed_nodes`, so this is only useful to pay the embedding cost up
    front (e.g. in a Makefile target) instead of on a rollout's first
    retrieval call.

    Returns:
        The number of embedded nodes.
    """
    client = client or EmbeddingClient()
    db = kuzu.Database(str(db_path), read_only=True)
    conn = kuzu.Connection(db)
    try:
        nodes, _ = _embed_nodes(conn, client, db_path)
        return len(nodes)
    finally:
        conn.close()
        db.close()


def retrieve(
    query: str,
    db_path: Path,
    client: EmbeddingClient | None = None,
    top_k: int = 5,
) -> list[Match]:
    """Retrieves the `top_k` catalog nodes most relevant to `query`, as triplets.

    Args:
        query: Natural-language question or description.
        db_path: Path to the on-disk Kùzu database built by kg_builder.
        client: EmbeddingClient to use; defaults to one configured from env.
        top_k: Number of matched nodes to return triplets for.

    Returns:
        Matches sorted by descending cosine similarity to `query`.
    """
    client = client or EmbeddingClient()
    db = kuzu.Database(str(db_path), read_only=True)
    conn = kuzu.Connection(db)
    try:
        nodes, vectors = _embed_nodes(conn, client, db_path)
        query_vector = client.embed([query])[0]

        scored = sorted(
            ((_cosine_similarity(query_vector, vectors[node_id]), node_id) for node_id in nodes),
            key=lambda pair: pair[0],
            reverse=True,
        )[:top_k]

        matches = []
        for similarity, node_id in scored:
            node = nodes[node_id]
            matches.append(
                Match(
                    node_type=node["type"],
                    node_id=node_id,
                    similarity=similarity,
                    triplets=_triplets_for_node(conn, node["type"], node["properties"]),
                )
            )
        return matches
    finally:
        conn.close()
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", type=str, nargs="?", help="Omit with --build-only.")
    parser.add_argument("--db-path", type=Path, default=Path("data_gen/kg.db"))
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--build-only", action="store_true", help="Only build/refresh the embeddings cache; no query needed."
    )
    args = parser.parse_args()

    if args.build_only:
        count = build_embeddings_cache(args.db_path)
        print(f"Embedded {count} nodes to {args.db_path}.embeddings.json")
    else:
        if not args.query:
            parser.error("query is required unless --build-only is given")
        for match in retrieve(args.query, args.db_path, top_k=args.top_k):
            print(f"\n{match.node_type} {match.node_id!r} (similarity={match.similarity:.3f})")
            for triplet in match.triplets:
                print(f"  {triplet}")
