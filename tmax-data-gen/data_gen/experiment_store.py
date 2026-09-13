"""Durable SQLite storage for paired prompt-benchmark rollouts."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from data_gen.prompt_variants import PromptVariant, task_case_hash


@dataclass(frozen=True)
class TaskCase:
    id: str
    task_dir: str
    task_case_sha256: str
    domain: str
    skill_type: str
    primitive_skill: str
    persona: str
    language: str


class ExperimentStore:
    """Append-only rollout records with immutable task and prompt identities."""

    def __init__(self, db_path: Path):
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(db_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize()

    def close(self) -> None:
        self.connection.close()

    def _initialize(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS experiments (
                run_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                solver_model TEXT NOT NULL,
                environment TEXT NOT NULL,
                agent_config_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_cases (
                case_id TEXT PRIMARY KEY,
                task_dir TEXT NOT NULL,
                task_case_sha256 TEXT NOT NULL,
                domain_id TEXT NOT NULL,
                skill_type_id TEXT NOT NULL,
                primitive_skill_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                language_id TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS prompt_variants (
                case_id TEXT NOT NULL REFERENCES task_cases(case_id),
                variant_id TEXT NOT NULL,
                kind TEXT NOT NULL,
                style TEXT NOT NULL,
                prompt_path TEXT NOT NULL,
                source_instruction_sha256 TEXT NOT NULL,
                prompt_sha256 TEXT NOT NULL,
                generator_model TEXT,
                PRIMARY KEY (case_id, variant_id)
            );
            CREATE TABLE IF NOT EXISTS rollout_runs (
                rollout_id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL REFERENCES experiments(run_id),
                case_id TEXT NOT NULL REFERENCES task_cases(case_id),
                variant_id TEXT NOT NULL,
                repetition INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                status TEXT NOT NULL,
                reward REAL,
                duration_seconds REAL NOT NULL,
                verifier_stdout TEXT,
                agent_exit_json TEXT,
                error_message TEXT,
                weave_trace_url TEXT,
                UNIQUE (run_id, case_id, variant_id, repetition),
                FOREIGN KEY (case_id, variant_id) REFERENCES prompt_variants(case_id, variant_id)
            );
            """
        )
        self.connection.commit()

    def register_experiment(self, run_id: str, solver_model: str, environment: str, agent_config: dict[str, Any]) -> None:
        self.connection.execute(
            "INSERT INTO experiments VALUES (?, ?, ?, ?, ?)",
            (run_id, datetime.now(UTC).isoformat(), solver_model, environment, json.dumps(agent_config, sort_keys=True)),
        )
        self.connection.commit()

    def register_task_case(self, task_dir: Path) -> TaskCase:
        metadata = json.loads((task_dir / "task_meta.json").read_text())
        digest = task_case_hash(task_dir)
        case = TaskCase(
            id=f"{metadata['task_name']}:{digest[:12]}",
            task_dir=str(task_dir.resolve()),
            task_case_sha256=digest,
            domain=metadata["domain"],
            skill_type=metadata["skill_type"],
            primitive_skill=metadata["primitive_skill"],
            persona=metadata["persona"],
            language=metadata["language"],
        )
        self.connection.execute(
            """INSERT OR IGNORE INTO task_cases VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case.id,
                case.task_dir,
                case.task_case_sha256,
                case.domain,
                case.skill_type,
                case.primitive_skill,
                case.persona,
                case.language,
            ),
        )
        self.connection.commit()
        return case

    def register_prompt_variant(self, case: TaskCase, variant: PromptVariant) -> None:
        self.connection.execute(
            """INSERT OR IGNORE INTO prompt_variants VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                case.id,
                variant.id,
                variant.kind,
                variant.style,
                str(variant.path.resolve()),
                variant.source_instruction_sha256,
                variant.text_sha256,
                variant.generator_model,
            ),
        )
        self.connection.commit()

    def record_rollout(
        self,
        *,
        run_id: str,
        case: TaskCase,
        variant: PromptVariant,
        repetition: int,
        started_at: str,
        finished_at: str,
        status: str,
        duration_seconds: float,
        reward: float | None = None,
        verifier_stdout: str | None = None,
        agent_exit: dict[str, Any] | None = None,
        error_message: str | None = None,
        weave_trace_url: str | None = None,
    ) -> None:
        self.connection.execute(
            """INSERT INTO rollout_runs (
                run_id, case_id, variant_id, repetition, started_at, finished_at,
                status, reward, duration_seconds, verifier_stdout, agent_exit_json,
                error_message, weave_trace_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id, case_id, variant_id, repetition) DO UPDATE SET
                started_at=excluded.started_at, finished_at=excluded.finished_at,
                status=excluded.status, reward=excluded.reward,
                duration_seconds=excluded.duration_seconds,
                verifier_stdout=excluded.verifier_stdout,
                agent_exit_json=excluded.agent_exit_json,
                error_message=excluded.error_message,
                weave_trace_url=excluded.weave_trace_url
            """,
            (
                run_id,
                case.id,
                variant.id,
                repetition,
                started_at,
                finished_at,
                status,
                reward,
                duration_seconds,
                verifier_stdout,
                json.dumps(agent_exit, sort_keys=True) if agent_exit is not None else None,
                error_message,
                weave_trace_url,
            ),
        )
        self.connection.commit()
