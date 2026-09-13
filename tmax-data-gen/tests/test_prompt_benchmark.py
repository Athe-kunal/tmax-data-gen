from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from data_gen.dashboard import summarize
from data_gen.experiment_store import ExperimentStore
from data_gen.prompt_variants import create_vague_variant, load_prompt_variant, task_case_hash
from data_gen.rollout import RolloutResult
from data_gen.run_experiment import run_experiment


def _make_task(root: Path) -> Path:
    task = root / "example-task"
    (task / "tests").mkdir(parents=True)
    (task / "environment").mkdir()
    (task / "instruction.md").write_text("Fix the import failure in /home/user/app.py.\n")
    (task / "tests" / "test.sh").write_text("#!/bin/bash\n")
    (task / "tests" / "test_final_state.py").write_text("def test_ok(): pass\n")
    (task / "environment" / "setup.sh").write_text("touch /home/user/app.py\n")
    (task / "task_meta.json").write_text(
        json.dumps(
            {
                "task_name": "example-task",
                "domain": "debugging",
                "skill_type": "diagnosis",
                "primitive_skill": "symptom-triage",
                "persona": "support-engineer",
                "language": "python",
                "truth": "private expected state",
                "setup_script": "touch /home/user/app.py",
            }
        )
    )
    return task


class PromptVariantTests(unittest.TestCase):
    def test_vague_variant_preserves_immutable_case_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            task = _make_task(Path(tmp))
            before = task_case_hash(task)
            vague_text = "An internal deployment now fails whenever it imports customer data. Please investigate the failure, find the cause, and restore normal processing for the affected customer team."
            with patch("data_gen.prompt_variants.render_vague_prompt", return_value=(vague_text, "test/model")):
                variant = create_vague_variant(task, "symptom-only")
            self.assertEqual("vague-symptom-only-v1", variant.id)
            self.assertEqual(vague_text + "\n", variant.text)
            self.assertEqual(before, task_case_hash(task))
            self.assertEqual(variant, load_prompt_variant(task, variant.id))

    def test_summary_identifies_precise_only_pass(self) -> None:
        rows = [
            {
                "case_id": "case-a",
                "variant_id": "precise-v1",
                "repetition": 0,
                "status": "completed",
                "reward": 1.0,
                "duration_seconds": 1.0,
                "domain_id": "debugging",
                "primitive_skill_id": "symptom-triage",
                "persona_id": "support-engineer",
                "language_id": "python",
            },
            {
                "case_id": "case-a",
                "variant_id": "vague-symptom-only-v1",
                "repetition": 0,
                "status": "completed",
                "reward": 0.0,
                "duration_seconds": 1.0,
                "domain_id": "debugging",
                "primitive_skill_id": "symptom-triage",
                "persona_id": "support-engineer",
                "language_id": "python",
            },
        ]
        metrics, pairs, _ = summarize(rows)
        self.assertEqual(1.0, metrics["precise_only_passes"])
        self.assertEqual("precise-only pass", pairs[0]["outcome"])

    def test_store_persists_a_rollout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = _make_task(root)
            store = ExperimentStore(root / "results.sqlite")
            try:
                store.register_experiment("run-1", "test/model", "sandbox", {})
                case = store.register_task_case(task)
                variant = load_prompt_variant(task)
                store.register_prompt_variant(case, variant)
                store.record_rollout(
                    run_id="run-1",
                    case=case,
                    variant=variant,
                    repetition=0,
                    started_at="2026-01-01T00:00:00+00:00",
                    finished_at="2026-01-01T00:00:01+00:00",
                    status="completed",
                    duration_seconds=1.0,
                    reward=1.0,
                )
                count = store.connection.execute("SELECT COUNT(*) FROM rollout_runs").fetchone()[0]
                self.assertEqual(1, count)
            finally:
                store.close()

    def test_batch_runner_records_matched_variants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task = _make_task(root)
            vague_text = "An internal deployment now fails whenever it imports customer data. Please investigate the failure, find the cause, and restore normal processing for the affected customer team."
            with patch("data_gen.prompt_variants.render_vague_prompt", return_value=(vague_text, "test/model")):
                create_vague_variant(task, "symptom-only")
            with patch(
                "data_gen.run_experiment.run_rollout",
                return_value=RolloutResult(
                    task_name="example-task",
                    prompt_variant_id="ignored-by-mock",
                    reward=1.0,
                    verifier_stdout="passed",
                    agent_exit={"exit_status": "Submitted"},
                ),
            ) as rollout:
                run_experiment(
                    tasks_dir=root,
                    db_path=root / "results.sqlite",
                    run_id="paired-run",
                    variants=["precise-v1", "vague-symptom-only-v1"],
                    repetitions=1,
                    environment="sandbox",
                    model=None,
                    raw_model="test/model",
                    agent_config={},
                )
            self.assertEqual(2, rollout.call_count)
            connection = sqlite3.connect(root / "results.sqlite")
            try:
                rows = connection.execute("SELECT variant_id, reward FROM rollout_runs ORDER BY variant_id").fetchall()
            finally:
                connection.close()
            self.assertEqual([("precise-v1", 1.0), ("vague-symptom-only-v1", 1.0)], rows)


if __name__ == "__main__":
    unittest.main()
