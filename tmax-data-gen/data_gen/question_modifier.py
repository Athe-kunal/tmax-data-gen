"""Rewrites a fully-specified gold task's `task_description` into a shorter,
less-prescriptive, "how a real person would actually ask it" version - for
evaluating how an agent handles underspecified requests instead of the
exhaustively detailed synthetic prompts `question_gen.generate_question`
produces.

The underspecification is meant to be load-bearing, not just terser prose:
detail a competent agent could recover itself by exploring the environment
and reasoning about the domain should be *cut*, so the question actually
tests whether the agent can figure that out - that's what makes it a good
eval question. Detail that's an arbitrary convention nothing in the
environment or domain knowledge could ever point to (an exact permission
mode, an exact output string, a byte-exact encoding choice) has to stay,
or the task just becomes an unfair guessing game against the generator's
arbitrary choices instead of a test of reasoning.

Deliberately touches nothing else: `truth`, `test_code`, and `setup_script`
stay exactly as collected, so the noisy question is graded by the exact same
verifier as the original - the noise is only in how the request is *phrased*,
never in what's actually required to pass. The prompt below is explicit
about that split (drop redundant formatting/verification-step prose freely;
never touch an identifier, path, or format the verifier checks exactly).

Single LLM call, same `litellm.completion` + XML-tag pattern as
`question_gen.generate_question`.
"""

from __future__ import annotations

import logging
import re

import litellm

from data_gen.weave_logger import weave_op

logger = logging.getLogger(__name__)

_SYSTEM_MSG = """\
You are simulating how a real, busy, non-expert user would actually phrase a \
request in a terminal-assistant chat - compared to the exhaustively detailed \
engineering ticket a synthetic data pipeline generated.

You will be given:
- <original_task>: the fully-specified task description (exact paths, exact \
formats, restated example transcripts, explicit verification steps, etc.)
- <truth>: the privileged ground truth an automated verifier checks against. \
It is completely fixed and the person asking would never see or state it \
themselves.

Rewrite the task as <noisy_task>: a shorter, more casual, less prescriptive \
version of the same request, the way someone would actually type it under \
time pressure - not a cleaned-up paraphrase of the ticket.

Two invariants govern every rewrite. Everything else is judgment calls in
service of these, not a checklist:

1. DISCOVERABILITY. The point of a noisy question isn't just brevity - it's \
that a capable agent should be expected to figure out missing detail by \
*exploring the environment and reasoning about the domain*, the way a real \
engineer would, rather than being handed a spec. So for every piece of \
information in <original_task>, ask: "could a competent agent recover this \
exact value by inspecting the files/state <truth> says already exist, plus \
ordinary domain reasoning - or is it an arbitrary choice nothing in the \
environment or domain knowledge could ever point to?"
   - Recoverable-by-exploration (DROP from the question, let the agent find \
it): the nature of a vulnerability in a file the agent can read; which named \
config parameters are missing, once the agent inspects the config; the \
general shape of a fix, once the agent understands the flaw. This is the \
good kind of vagueness - it's what makes the question worth asking.
   - Truly arbitrary (KEEP verbatim, no rewording/rounding/"roughly"): a \
numeric threshold, permission mode, byte-exact fixture, exact output \
string/schema, or encoding convention that the synthetic generator simply \
picked - nothing in the environment or in domain expertise would lead an \
agent to that specific value instead of an equally reasonable alternative. \
Stripping these doesn't test reasoning, it turns the task into an unfair \
guessing game against the generator's arbitrary choices. When genuinely \
unsure which bucket something is in, keep it - an unresolvable detail is a \
worse failure than an under-compressed sentence.

Two shapes of "truly arbitrary" are easy to miss because attention tends to \
go to the task's main deliverable and skip past supporting detail - watch \
for both explicitly:
   - Secondary/auxiliary artifacts. A task's *primary* output is only one \
of possibly several things graded - a log file, manifest, report, index, or \
generated cert alongside it is exactly as arbitrary and exactly as checked. \
Compressing the paragraph that describes the primary deliverable and \
silently dropping the sentence that names a secondary one (its exact \
filename, its exact required content) is the single most common mistake to \
avoid.
   - Structured-output field/key names. When the deliverable is JSON, CSV, \
or another structured format, every field/column/key name in it is an \
arbitrary choice the generator made - there is no way to derive that the \
key should be called `top_author_id` rather than `topAuthorId` or \
`author_id` from domain reasoning alone. Keep every such name exactly as \
given, even while shortening the sentence around it.

2. NO LEAKAGE. This is the same rule that already governs the <task>/<truth> \
split when this pipeline first generates a question: the request must never \
state or imply the answer to whatever the agent is being asked to figure \
out. If <original_task> shows a placeholder for something the agent must \
determine (a redacted field, a "TBD", a blank), <noisy_task> keeps it as an \
unresolved placeholder too - never substitute the real value from <truth>, \
even though you can see it. Determining that value *is* the task.

Style-wise, you MAY: use vaguer, more natural, less structured language \
(incomplete sentences, hedging, a minor typo); add a little irrelevant \
scene-setting noise (being busy, a stray aside - actual noise, not signal); \
reorder points or leave something obvious to be inferred; and drop an \
abstract format spec when a concrete literal example already covers the \
same ground under invariant 1. Be aggressive about compression, not just \
tone - a real person does not spec a format twice, does not narrate their \
own numbered step list, does not explain how they'll grade the answer. If \
<noisy_task> still reads like a cleaned-up version of the ticket rather than \
someone dashing off a request, you haven't compressed enough.

Respond in XML:
<noisy_task>
    The rewritten, shorter, noisier task description.
</noisy_task>"""

_USER_TEMPLATE = """\
<original_task>
{task_description}
</original_task>

<truth>
{truth}
</truth>

Rewrite <original_task> as described."""


def _parse_noisy_task(raw: str) -> str:
    match = re.search(r"<noisy_task>(.*?)</noisy_task>", raw, re.DOTALL)
    if not match or not match.group(1).strip():
        raise ValueError(f"No <noisy_task> block found in response:\n{raw}")
    return match.group(1).strip()


def _retry(fn, max_retries: int, description: str):
    last_error: Exception | None = None
    for attempt in range(1 + max_retries):
        try:
            return fn()
        except ValueError as e:
            last_error = e
            logger.warning("%s failed (attempt %d/%d): %s", description, attempt + 1, 1 + max_retries, e)
    raise last_error


@weave_op
def generate_noisy_question(
    task_description: str,
    truth: str,
    model: str,
    temperature: float = 1.0,
    max_tokens: int = 8192,
    extra_kwargs: dict[str, object] | None = None,
    max_retries: int = 2,
) -> str:
    """Rewrites `task_description` into a shorter, less-specified version.

    Args:
        task_description: The original, fully-specified task text (a gold
            task's `task_meta.json["task_description"]`).
        truth: That same task's privileged truth - given so the rewrite
            never drops or contradicts anything the (unchanged) verifier
            actually checks.
        model: LiteLLM model string.
        temperature: Sampling temperature.
        max_tokens: Max tokens for the call.
        extra_kwargs: Extra kwargs merged into the `litellm.completion` call
            (e.g. `api_base`/`api_key` for an OpenAI-compatible endpoint).
        max_retries: Re-sample attempts if the response fails to parse.

    Returns:
        The rewritten, noisier task description. `truth`/tests/setup are
        unchanged - only pair this text back with the original task's own
        `truth`/`test_code`/`setup_script` when using it.
    """
    extra_kwargs = extra_kwargs or {}

    def _call() -> str:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM_MSG},
                {"role": "user", "content": _USER_TEMPLATE.format(task_description=task_description, truth=truth)},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_kwargs,
        )
        return _parse_noisy_task(response.choices[0].message.content or "")

    return _retry(_call, max_retries, "noisy question generation")


def _iter_gold_task_dirs(root: Path) -> list[Path]:
    """A `root` that itself has a task_meta.json is treated as one task;
    otherwise every immediate child with a task_meta.json is used."""
    if (root / "task_meta.json").exists():
        return [root]
    return sorted(p for p in root.iterdir() if p.is_dir() and (p / "task_meta.json").exists())


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    from data_gen.inference_config import OpenAICompatibleConfig

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "gold_task_dir",
        type=Path,
        help="A gold_tasks/<task> directory (has task_meta.json), or a gold_tasks/ "
        "directory itself to run every task in it.",
    )
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    parser.add_argument(
        "--out-file",
        type=Path,
        default=None,
        help="Write {task_name: {original, noisy}} JSON here for review, instead of printing. "
        "Required in batch mode (a directory of many tasks).",
    )
    args = parser.parse_args()

    if args.raw_model:
        litellm_model, model_kwargs = args.raw_model, {}
    else:
        inference_config = OpenAICompatibleConfig.from_env(model=args.model)
        litellm_model, model_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    task_dirs = _iter_gold_task_dirs(args.gold_task_dir)
    if not task_dirs:
        raise SystemExit(f"No task_meta.json found under {args.gold_task_dir}")
    if len(task_dirs) > 1 and args.out_file is None:
        raise SystemExit(f"{len(task_dirs)} tasks found under {args.gold_task_dir} - pass --out-file for batch mode.")

    results: dict[str, dict[str, str]] = {}
    for i, task_dir in enumerate(task_dirs):
        print(f"[{i + 1}/{len(task_dirs)}] {task_dir.name}")
        meta = json.loads((task_dir / "task_meta.json").read_text())
        try:
            noisy = generate_noisy_question(meta["task_description"], meta["truth"], litellm_model, extra_kwargs=model_kwargs)
        except ValueError as e:
            print(f"  FAILED: {e}")
            results[task_dir.name] = {"original": meta["task_description"], "noisy": None, "error": str(e)}
            continue
        results[task_dir.name] = {"original": meta["task_description"], "noisy": noisy}

    if args.out_file:
        args.out_file.parent.mkdir(parents=True, exist_ok=True)
        args.out_file.write_text(json.dumps(results, indent=2))
        print(f"\nWrote {len(results)} results to {args.out_file}")
    else:
        task_name, pair = next(iter(results.items()))
        print("=== ORIGINAL task_description ===")
        print(pair["original"])
        print("\n=== NOISY task_description ===")
        print(pair["noisy"])
