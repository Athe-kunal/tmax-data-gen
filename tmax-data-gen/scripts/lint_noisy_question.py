"""Flags literal constants a gold task's verifier checks that vanished from
a `question_modifier`-rewritten noisy question - a fast pre-filter for
manual review, not a pass/fail gate.

`question_modifier.generate_noisy_question` is instructed to keep every
"truly arbitrary" detail (exact paths, permission modes, output-schema
field names, secondary-artifact filenames, ...) verbatim, but a ~70B model
doesn't apply that reliably 100% of the time - confirmed by hand across
several gold tasks. This script automates the first pass of that check: it
pulls every string literal `tests/test_final_state.py` asserts on, and
reports which of the ones that were present in the *original* task
description are missing from the *noisy* one. A flag here doesn't mean the
noisy question is broken (many literals are innocuous, or recoverable by
reading the environment) - it means a human should look at that one line.

Usage:
    python -m scripts.lint_noisy_question noisy_questions.json \\
        --gold-tasks-dir gold_tasks [task_name ...]

`noisy_questions.json` is the `--out-file` produced by
`data_gen.question_modifier`'s batch mode: {task_name: {original, noisy}}.
Omit trailing task names to check every task in the file.
"""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

_MIN_LITERAL_LEN = 4
_IGNORE_PREFIXES = ("test_", "/logs/", "def ", "assert")


def literals_from_test(test_path: Path) -> list[str]:
    """Every string constant in a pytest file that looks like an asserted-on value."""
    try:
        tree = ast.parse(test_path.read_text())
    except SyntaxError:
        return []
    literals = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            s = node.value
            if len(s) >= _MIN_LITERAL_LEN and not s.isspace() and "\n" not in s and not s.startswith(_IGNORE_PREFIXES):
                literals.append(s)
    return literals


def dropped_literals(original: str, noisy: str, test_path: Path) -> list[str]:
    """Literals the verifier checks that were in `original` but not `noisy`."""
    literals = literals_from_test(test_path)
    present_in_original = [l for l in literals if l in original]
    return [l for l in present_in_original if l not in noisy]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("noisy_questions_json", type=Path)
    parser.add_argument("--gold-tasks-dir", type=Path, default=Path("gold_tasks"))
    parser.add_argument("task_names", nargs="*", help="Subset to check; default is every task in the JSON.")
    args = parser.parse_args()

    noisy_questions = json.loads(args.noisy_questions_json.read_text())
    names = args.task_names or sorted(noisy_questions)

    total_flags = 0
    for name in names:
        entry = noisy_questions.get(name)
        if not entry or not entry.get("noisy"):
            continue
        test_path = args.gold_tasks_dir / name / "tests" / "test_final_state.py"
        if not test_path.exists():
            continue
        dropped = dropped_literals(entry["original"], entry["noisy"], test_path)
        if dropped:
            total_flags += len(dropped)
            print(f"=== {name} ===")
            for literal in dropped:
                print(f"  DROPPED literal: {literal!r}")

    print(f"\n{total_flags} flags across {len(names)} tasks checked.")
