"""Rewrites a fully-specified gold task's `task_description` into a shorter,
less-prescriptive, "how a real person would actually ask it" version - for
evaluating how an agent handles underspecified requests instead of the
exhaustively detailed synthetic prompts `question_gen.generate_question`
produces.

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

You MAY:
* Compress or drop exhaustive formatting specs, restated example \
transcripts, and explicit "verification steps" instructions (a real user \
wouldn't spell out how they'll grade the answer).
* Use vaguer, more natural, less structured language - incomplete \
sentences, a little hedging ("I think", "not 100% sure but..."), maybe a \
minor typo.
* Add a little irrelevant scene-setting noise (being busy, a stray aside) - \
actual noise, not signal.
* Reorder points, or leave something to be inferred that's obvious from \
context.

Be aggressive about compression, not just tone. A real person does not \
carefully spec a format twice - once abstractly ("KEY=VALUE, one per \
line...") and again as a concrete example. If <original_task> gives both an \
abstract template AND a literal example that covers the same information, \
DROP the abstract template and keep only the literal example (verbatim, per \
the MUST-NOT rule below) - let the example itself imply the format, the way \
someone dashing off a request actually would ("like this:" + one example, \
not a spec). Cut numbered/lettered step lists down to a couple of plain \
sentences. If you find yourself keeping most of the original's structure and \
length, you have not compressed enough - aim for roughly half the length or \
shorter, not just softer wording of the same content.

You MUST NOT:
* Change, weaken, or omit any concrete identifier the verifier depends on \
exactly as-is: exact file/directory paths, exact filenames the agent must \
create, exact function/table/index/column names, exact output formats or \
schemas that are mechanically checked, exact numeric values or literal \
strings <truth> fixes.
* Paraphrase, summarize, or drop any literal example/fixture content given \
verbatim in <original_task> (e.g. an exact sample file's contents in a code \
block) if <truth> shows the verifier checks that exact content byte-for-byte \
- copy it into <noisy_task> completely unchanged, character for character, \
even while shortening the prose around it. When in doubt about whether an \
example is checked exactly, keep it verbatim - dropping it is the more \
dangerous mistake.
* Introduce any new requirement, constraint, or claimed fact that \
contradicts <truth>.
* Leave it ambiguous *what deliverable* is being graded - vague about *how* \
is fine and expected; vague about *which file/output* is checked is not.
* LEAK THE ANSWER: if <original_task> shows an example/expected-output \
snippet with a placeholder for something the agent is supposed to figure \
out (e.g. `"CWE-XXX"`, `<count>`, `TBD`, a blank), keep that field as the \
same kind of placeholder in <noisy_task> - never replace it with the real \
value from <truth>, even though you can see it. The whole point of that \
field being a placeholder is that solving it *is* the task; filling it in \
gives the answer away.
* Drop or soften an exact formula, threshold, parameter, or procedure that \
<truth> shows determines the one correct output (e.g. "anomalies are >3 \
standard deviations from the mean of the previous 30 values", "RSA-2048 \
with sha256"). This is different from the abstract-vs-concrete-example \
compression above: dropping a redundant format template loses nothing \
because the concrete example still pins it down, but dropping an exact \
algorithmic parameter with no other place it's pinned down makes the \
*correct answer itself* underdetermined, not just the phrasing vaguer. Cut \
prose, never cut the numbers/procedure a correct solution depends on.

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


if __name__ == "__main__":
    import argparse
    import json
    from pathlib import Path

    from data_gen.inference_config import OpenAICompatibleConfig

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gold_task_dir", type=Path, help="A gold_tasks/<task> directory (has task_meta.json).")
    parser.add_argument("--model", type=str, default=None)
    parser.add_argument("--raw-model", type=str, default=None)
    args = parser.parse_args()

    meta = json.loads((args.gold_task_dir / "task_meta.json").read_text())

    if args.raw_model:
        litellm_model, model_kwargs = args.raw_model, {}
    else:
        inference_config = OpenAICompatibleConfig.from_env(model=args.model)
        litellm_model, model_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    noisy = generate_noisy_question(meta["task_description"], meta["truth"], litellm_model, extra_kwargs=model_kwargs)

    print("=== ORIGINAL task_description ===")
    print(meta["task_description"])
    print("\n=== NOISY task_description ===")
    print(noisy)
