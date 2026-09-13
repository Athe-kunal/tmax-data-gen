"""Renders the Kùzu knowledge graph to a static PNG image.

Reuses `kg_export.export_graph`, so it stays generic to whatever node/rel
tables kg_builder produced - node color/size are keyed by each node's
`type` (its Kùzu table name), discovered at render time rather than
hardcoded to today's 10 axes.

Layout is delegated to Graphviz's `sfdp` (a force-directed engine built for
large sparse graphs) via a generated DOT file, rather than networkx's naive
spring layout - with hundreds of degree-1 leaf nodes (e.g. PrimitiveSkills),
a plain spring layout tends to collapse them into a uniform outer ring
since nothing but global repulsion positions them. sfdp's multilevel
approach clusters leaves near their actual parent instead.

Requires the Graphviz `sfdp` binary to be installed (`apt install graphviz`
/ `brew install graphviz`).

Usage:
    uv run python -m data_gen.kg_visualize \
        --db-path tmax-data-gen/data_gen/kg.db \
        --out assets/knowledge_graph.png
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from data_gen.kg_export import export_graph

# A qualitative, colorblind-friendlier palette (Tableau10), assigned to
# node types by descending node count so the biggest groups get the most
# distinct hues. Falls back to gray for any type beyond the palette's size.
_PALETTE = [
    "#4e79a7", "#f28e2b", "#e15759", "#76b7b2", "#59a14f",
    "#edc948", "#b07aa1", "#ff9da7", "#9c755f", "#bab0ac",
]
_FALLBACK_COLOR = "#7a7a86"

_BG = "#0b0b0f"
_FG = "#f0f0f3"
_DIM = "#9a9aa4"

# Node width (inches, Graphviz `width`/`height`) by how "hub-like" a type
# typically is; overridden per-type below by rank (biggest count -> smallest
# node), so leaves stay small and hubs stay legible regardless of the axes.
_MIN_WIDTH, _MAX_WIDTH = 0.09, 0.55
# Types with at most this many nodes get text labels drawn on them.
_MAX_LABELED_COUNT = 15


def _node_label(properties: dict) -> str:
    return str(properties.get("label") or properties.get("name") or properties.get("value") or "")


def _escape_dot(text: str) -> str:
    return text.replace("\\", "\\\\").replace('"', '\\"')


def _build_dot(graph: dict) -> tuple[str, dict[str, str], dict[str, int]]:
    """Returns (dot_source, color_by_type, count_by_type)."""
    type_counts: dict[str, int] = {}
    for node in graph["nodes"]:
        type_counts[node["type"]] = type_counts.get(node["type"], 0) + 1
    types_by_size = sorted(type_counts, key=type_counts.get, reverse=True)
    color_of = {t: _PALETTE[i] if i < len(_PALETTE) else _FALLBACK_COLOR for i, t in enumerate(types_by_size)}

    n_types = len(types_by_size)
    width_of = {
        t: _MAX_WIDTH - (_MAX_WIDTH - _MIN_WIDTH) * (rank / max(n_types - 1, 1))
        for rank, t in enumerate(types_by_size)
    }

    lines = [
        "graph G {",
        f'  bgcolor="{_BG}";',
        "  outputorder=edgesfirst;",
        f'  node [style=filled, fontcolor="{_FG}", fontname="Helvetica", color="{_BG}", shape=circle, fixedsize=true];',
        f'  edge [color="{_DIM}55", penwidth=0.6];',
    ]
    for node in graph["nodes"]:
        node_type = node["type"]
        show_label = type_counts[node_type] <= _MAX_LABELED_COUNT
        label = _escape_dot(_node_label(node["properties"])) if show_label else ""
        width = width_of[node_type]
        font_size = 11 if show_label else 1
        lines.append(
            f'  "{node["id"]}" [label="{label}", fillcolor="{color_of[node_type]}", '
            f'width={width:.3f}, height={width:.3f}, fontsize={font_size}];'
        )
    for edge in graph["edges"]:
        lines.append(f'  "{edge["source"]}" -- "{edge["target"]}";')
    lines.append("}")
    return "\n".join(lines), color_of, type_counts


def _run_sfdp(dot_source: str, out_png: Path) -> None:
    if shutil.which("sfdp") is None:
        raise RuntimeError("Graphviz's `sfdp` binary was not found on PATH. Install the `graphviz` package.")
    with tempfile.NamedTemporaryFile("w", suffix=".dot", delete=False) as f:
        f.write(dot_source)
        dot_path = f.name
    try:
        subprocess.run(
            [
                "sfdp", "-Tpng", "-Goverlap=prism", "-Gsep=+6", "-Gsplines=curved",
                f"-Gdpi=150", dot_path, "-o", str(out_png),
            ],
            check=True, capture_output=True, text=True,
        )
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"sfdp failed: {e.stderr}") from e
    finally:
        Path(dot_path).unlink(missing_ok=True)


def _composite_title_and_legend(
    png_path: Path, title: str, color_of: dict[str, str], type_counts: dict[str, int]
) -> None:
    """Draws a title (top-left) and type legend (bottom-left) onto the PNG in place."""
    image = Image.open(png_path).convert("RGBA")
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    try:
        title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 26)
        legend_font = ImageFont.truetype("DejaVuSans.ttf", 18)
    except OSError:
        title_font = ImageFont.load_default()
        legend_font = ImageFont.load_default()

    margin = 24
    draw.text((margin, margin), title, font=title_font, fill=_FG)

    types_by_size = sorted(type_counts, key=type_counts.get, reverse=True)
    row_height = 26
    legend_top = image.height - margin - row_height * len(types_by_size)
    for i, node_type in enumerate(types_by_size):
        y = legend_top + i * row_height
        color = color_of[node_type]
        draw.ellipse([margin, y + 6, margin + 12, y + 18], fill=color)
        draw.text(
            (margin + 20, y),
            f"{node_type} ({type_counts[node_type]})",
            font=legend_font, fill=_FG,
        )

    combined = Image.alpha_composite(image, overlay)
    combined.convert("RGB").save(png_path)


def render(db_path: Path, out_path: Path) -> None:
    """Renders the knowledge graph at `db_path` to a PNG at `out_path`."""
    graph = export_graph(db_path)
    dot_source, color_of, type_counts = _build_dot(graph)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _run_sfdp(dot_source, out_path)

    title = f"TMax Knowledge Graph — {len(graph['nodes'])} nodes, {len(graph['edges'])} edges"
    _composite_title_and_legend(out_path, title, color_of, type_counts)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db-path", type=Path, default=Path("tmax-data-gen/data_gen/kg.db"))
    parser.add_argument("--out", type=Path, default=Path("assets/knowledge_graph.png"))
    args = parser.parse_args()

    render(args.db_path, args.out)
    print(f"Wrote {args.out}")
