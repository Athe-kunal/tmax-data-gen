"""Local dashboard for paired precise and vague prompt benchmark results."""

from __future__ import annotations

import argparse
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


def _rows(connection: sqlite3.Connection, run_id: str) -> list[dict[str, Any]]:
    cursor = connection.execute(
        """SELECT r.run_id, r.case_id, r.variant_id, r.repetition, r.status, r.reward,
                  r.duration_seconds, r.error_message, r.weave_trace_url,
                  c.domain_id, c.primitive_skill_id, c.persona_id, c.language_id
           FROM rollout_runs r JOIN task_cases c ON c.case_id = r.case_id
           WHERE r.run_id = ?
           ORDER BY c.domain_id, r.case_id, r.repetition, r.variant_id""",
        (run_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def _is_completed(row: dict[str, Any]) -> bool:
    return row["status"] == "completed" and row["reward"] is not None


def _outcome(precise: dict[str, Any] | None, vague: dict[str, Any] | None) -> str:
    if precise is None or vague is None or not _is_completed(precise) or not _is_completed(vague):
        return "incomplete"
    if precise["reward"] == 1 and vague["reward"] == 1:
        return "both pass"
    if precise["reward"] == 1:
        return "precise-only pass"
    if vague["reward"] == 1:
        return "vague-only pass"
    return "both fail"


def summarize(rows: list[dict[str, Any]]) -> tuple[dict[str, float], list[dict[str, Any]], list[dict[str, Any]]]:
    """Build aggregate metrics without treating infrastructure errors as task failures."""
    by_variant: dict[str, list[dict[str, Any]]] = defaultdict(list)
    pairs: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        by_variant[row["variant_id"]].append(row)
        pairs[(row["case_id"], row["repetition"])][row["variant_id"]] = row

    metrics: dict[str, float] = {"total_rollouts": float(len(rows))}
    for variant_id, variant_rows in by_variant.items():
        completed = [row for row in variant_rows if _is_completed(row)]
        metrics[f"{variant_id}_pass_rate"] = sum(row["reward"] for row in completed) / len(completed) if completed else 0.0
        metrics[f"{variant_id}_completed_count"] = float(len(completed))
        metrics[f"{variant_id}_attempt_count"] = float(len(variant_rows))
        metrics[f"{variant_id}_error_count"] = float(sum(row["status"] != "completed" for row in variant_rows))

    pair_rows: list[dict[str, Any]] = []
    for (case_id, repetition), pair in sorted(pairs.items()):
        precise = pair.get("precise-v1")
        vague = next((row for variant, row in pair.items() if variant.startswith("vague-")), None)
        if precise is None and vague is None:
            continue
        reference = precise or vague
        assert reference is not None
        outcome = _outcome(precise, vague)
        pair_rows.append({
            "case_id": case_id, "repetition": repetition, "domain": reference["domain_id"],
            "skill": reference["primitive_skill_id"], "language": reference["language_id"],
            "precise_status": precise["status"] if precise else "missing",
            "precise_reward": precise["reward"] if precise else None,
            "vague_status": vague["status"] if vague else "missing",
            "vague_reward": vague["reward"] if vague else None,
            "precise_seconds": round(precise["duration_seconds"], 2) if precise else None,
            "vague_seconds": round(vague["duration_seconds"], 2) if vague else None,
            "outcome": outcome, "is_valid_pair": outcome != "incomplete",
        })
    valid_pairs = [row for row in pair_rows if row["is_valid_pair"]]
    metrics["pair_count"] = float(len(pair_rows))
    metrics["valid_pair_count"] = float(len(valid_pairs))
    metrics["incomplete_pair_count"] = float(len(pair_rows) - len(valid_pairs))
    metrics["precise_only_passes"] = float(sum(row["outcome"] == "precise-only pass" for row in valid_pairs))
    metrics["infrastructure_errors"] = float(sum(row["status"] != "completed" for row in rows))
    return metrics, pair_rows, rows


def _inject_styles(st: Any) -> None:
    st.markdown("""<style>
    .stApp { background: #fafbfc; color: #172033; }
    .block-container { max-width: 1160px; padding-top: 3.25rem; padding-bottom: 3rem; }
    h1 { color: #172033; font-size: 2.15rem !important; font-weight: 720 !important; letter-spacing: -.045em; margin-bottom: .25rem !important; }
    .run-note { color: #64748b; font-size: .92rem; margin: -.1rem 0 1.25rem; }
    .metric-card { background: #ffffff; border: 1px solid #e3e8ef; border-radius: 12px; padding: 1.05rem 1.15rem; min-height: 116px; box-shadow: 0 1px 2px rgba(15, 23, 42, .035); }
    .metric-label { color: #64748b; font-size: .78rem; font-weight: 650; letter-spacing: .04em; text-transform: uppercase; }
    .metric-value { color: #172033; font-size: 1.9rem; font-weight: 730; letter-spacing: -.045em; line-height: 1.25; margin-top: .32rem; }
    .metric-note { color: #7b8798; font-size: .83rem; margin-top: .18rem; }
    .section-title { color: #172033; font-size: 1.08rem; font-weight: 680; margin: 2rem 0 .55rem; }
    div[data-testid="stDataFrame"] { border: 1px solid #e3e8ef; border-radius: 10px; overflow: hidden; }
    .stSelectbox label { color: #475569 !important; font-size: .9rem !important; }
    div[data-testid="stAlert"] { border-radius: 10px; }
    </style>""", unsafe_allow_html=True)


def _card(st: Any, label: str, value: str, note: str) -> None:
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)


def _display_rows(pair_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "Domain": row["domain"], "Skill": row["skill"],
        "Precise": "pass" if row["precise_reward"] == 1 else row["precise_status"],
        "Vague": "pass" if row["vague_reward"] == 1 else row["vague_status"],
        "Outcome": row["outcome"], "Precise time": row["precise_seconds"],
        "Vague time": row["vague_seconds"], "Case": row["case_id"],
    } for row in pair_rows]


def _model_label(model: str) -> str:
    """Turn provider model IDs into a compact label for the dashboard."""
    return model.rsplit("/", 1)[-1].replace("-", " ")


def main() -> None:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--db-path", type=Path, default=Path("runs/tmax_results.sqlite"))
    args, _ = parser.parse_known_args()
    import streamlit as st

    st.set_page_config(page_title="TMAX Prompt Robustness", page_icon="◈", layout="wide")
    _inject_styles(st)
    if not args.db_path.is_file():
        st.error(f"No experiment database exists at {args.db_path}")
        st.stop()
    st.title("Vague vs Precise Bench")
    st.markdown(
        '<div class="run-note">Compare the same task with a detailed prompt and a vague prompt.</div>',
        unsafe_allow_html=True,
    )
    connection = sqlite3.connect(args.db_path)
    connection.row_factory = sqlite3.Row
    try:
        experiments = [
            dict(row)
            for row in connection.execute(
                "SELECT run_id, solver_model AS model, environment, created_at "
                "FROM experiments ORDER BY created_at DESC"
            )
        ]
        if not experiments:
            st.info("No experiments have been recorded yet.")
            st.stop()
        labels = {item["run_id"]: item["run_id"] for item in experiments}
        run_column, model_column = st.columns([4, 1])
        with run_column:
            run_id = st.selectbox(
                "Benchmark run",
                list(labels),
                format_func=labels.get,
                label_visibility="collapsed",
            )
        experiment = next(item for item in experiments if item["run_id"] == run_id)
        with model_column:
            st.caption("Model")
            st.write(f"**{_model_label(experiment['model'])}**")
        metrics, pair_rows, raw_rows = summarize(_rows(connection, run_id))
    finally:
        connection.close()

    precise_done, precise_attempts = int(metrics.get("precise-v1_completed_count", 0)), int(metrics.get("precise-v1_attempt_count", 0))
    precise_rate = metrics.get("precise-v1_pass_rate", 0.0)
    vague_variant = next((key.removesuffix("_pass_rate") for key in metrics if key.startswith("vague-") and key.endswith("_pass_rate")), None)
    vague_done = int(metrics.get(f"{vague_variant}_completed_count", 0)) if vague_variant else 0
    vague_attempts = int(metrics.get(f"{vague_variant}_attempt_count", 0)) if vague_variant else 0
    vague_rate = metrics.get(f"{vague_variant}_pass_rate", 0.0) if vague_variant else 0.0
    valid_pairs, pair_count = int(metrics["valid_pair_count"]), int(metrics["pair_count"])
    if valid_pairs:
        precise_paired = sum(row["precise_reward"] for row in pair_rows if row["is_valid_pair"]) / valid_pairs
        vague_paired = sum(row["vague_reward"] for row in pair_rows if row["is_valid_pair"]) / valid_pairs
        gap_value, gap_note = f"{precise_paired - vague_paired:+.0%}", "precise minus vague on valid pairs"
    else:
        gap_value, gap_note = "—", "no fully completed pairs yet"

    first, second, third, fourth = st.columns(4)
    with first: _card(st, "Precise prompt", f"{precise_rate:.0%}", f"{precise_done} of {precise_attempts} completed")
    with second: _card(st, "Vague prompt", f"{vague_rate:.0%}", f"{vague_done} of {vague_attempts} completed")
    with third: _card(st, "Compared tasks", f"{valid_pairs}/{pair_count}", "both prompts completed")
    with fourth: _card(st, "Difference", gap_value, "precise compared with vague")
    st.markdown('<div class="section-title">Results by task</div>', unsafe_allow_html=True)
    st.dataframe(
        _display_rows(pair_rows),
        use_container_width=True,
        hide_index=True,
        height=36 + 35 * min(10, max(1, len(pair_rows))),
    )
    if metrics["infrastructure_errors"]:
        st.warning(f"{int(metrics['infrastructure_errors'])} rollout attempt(s) did not complete. They are excluded from the prompt-gap calculation.")


if __name__ == "__main__":
    main()
