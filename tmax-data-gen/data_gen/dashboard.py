"""Local dashboard for matched precise and vague prompt benchmark results.

Run with:
    uv run streamlit run tmax-data-gen/data_gen/dashboard.py -- --db-path runs/tmax_results.sqlite
"""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


def _rows(connection: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    cursor = connection.execute(
        """
        SELECT r.run_id, r.case_id, r.variant_id, r.repetition, r.status, r.reward,
               r.duration_seconds, r.error_message, r.weave_trace_url,
               c.domain_id, c.primitive_skill_id, c.persona_id, c.language_id
        FROM rollout_runs r
        JOIN task_cases c ON c.case_id = r.case_id
        WHERE r.run_id = ?
        ORDER BY c.domain_id, r.case_id, r.repetition, r.variant_id
        """,
        (run_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def summarize(rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]], list[dict[str, Any]]]:
    """Builds aggregate metrics and matched precise-vague case rows."""
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_variant[row["variant_id"]].append(row)
        pairs[(row["case_id"], row["repetition"])][row["variant_id"]] = row

    metrics: dict[str, float] = {"total_rollouts": float(len(rows))}
    for variant_id, variant_rows in by_variant.items():
        completed = [row for row in variant_rows if row["status"] == "completed" and row["reward"] is not None]
        metrics[f"{variant_id}_pass_rate"] = (
            sum(row["reward"] for row in completed) / len(completed) if completed else 0.0
        )
        metrics[f"{variant_id}_count"] = float(len(completed))

    pair_rows: list[dict[str, Any]] = []
    for (case_id, repetition), pair in sorted(pairs.items()):
        precise = pair.get("precise-v1")
        vague = next((row for variant, row in pair.items() if variant.startswith("vague-")), None)
        if precise is None or vague is None:
            continue
        if precise["status"] != "completed" or vague["status"] != "completed":
            outcome = "incomplete"
        elif precise["reward"] == 1 and vague["reward"] == 1:
            outcome = "both pass"
        elif precise["reward"] == 1:
            outcome = "precise-only pass"
        elif vague["reward"] == 1:
            outcome = "vague-only pass"
        else:
            outcome = "both fail"
        pair_rows.append(
            {
                "case_id": case_id,
                "repetition": repetition,
                "domain": precise["domain_id"],
                "skill": precise["primitive_skill_id"],
                "language": precise["language_id"],
                "precise_reward": precise["reward"],
                "vague_reward": vague["reward"],
                "precise_seconds": round(precise["duration_seconds"], 2),
                "vague_seconds": round(vague["duration_seconds"], 2),
                "outcome": outcome,
            }
        )
    metrics["matched_pairs"] = float(len(pair_rows))
    metrics["precise_only_passes"] = float(sum(row["outcome"] == "precise-only pass" for row in pair_rows))
    return metrics, pair_rows, rows


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--db-path", type=Path, default=Path("runs/tmax_results.sqlite"))
    args, _ = parser.parse_known_args()

    import streamlit as st

    st.set_page_config(page_title="TMAX prompt benchmark", layout="wide")
    st.title("TMAX prompt benchmark")
    if not args.db_path.is_file():
        st.error(f"No experiment database exists at {args.db_path}")
        st.stop()
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        run_ids = [row[0] for row in connection.execute("SELECT run_id FROM experiments ORDER BY created_at DESC")]
        if not run_ids:
            st.info("No experiments have been recorded yet.")
            st.stop()
        run_id = st.sidebar.selectbox("Experiment", run_ids)
        metrics, pair_rows, raw_rows = summarize(_rows(connection, run_id))
    finally:
        connection.close()

    precise_rate = metrics.get("precise-v1_pass_rate", 0.0)
    vague_rates = [value for key, value in metrics.items() if key.startswith("vague-") and key.endswith("_pass_rate")]
    vague_rate = vague_rates[0] if vague_rates else 0.0
    first, second, third, fourth = st.columns(4)
    first.metric("Precise pass rate", f"{precise_rate:.1%}")
    second.metric("Vague pass rate", f"{vague_rate:.1%}")
    third.metric("Matched pairs", int(metrics["matched_pairs"]))
    fourth.metric("Precise-only passes", int(metrics["precise_only_passes"]))

    st.subheader("Matched task outcomes")
    st.dataframe(pair_rows, use_container_width=True, hide_index=True)
    st.subheader("All rollout records")
    st.dataframe(raw_rows, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
