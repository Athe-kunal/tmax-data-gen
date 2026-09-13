"""Generates one full-spec question from a sampled catalog entry.

Two-call pipeline (mirrors tmax's legacy `task_template_gen.py` /
`completion_test_gen.py` split):

  1. Task+truth call: given the sampled Domain/SkillType/Primitive/
     Persona/Language and prior "context till now" (previously generated
     task descriptions, so the model can avoid repeats), emit a `<task>`
     (public instruction) and `<truth>` (privileged ground truth that must
     never leak into `<task>`) as XML.
  2. Test call: given the task description and truth, emit a
     `test_final_state.py` pytest suite that passes only if the task was
     solved correctly.

Both calls go through `litellm.completion` directly (not mini-swe-agent's
`LitellmModel`, which forces a bash tool-call loop unsuited to a plain text
completion). `generate_question` is provider-agnostic: pass `extra_kwargs`
to route through a specific backend (e.g. `WeaveInferenceConfig.from_env().
litellm_kwargs()` for W&B Weave Inference - see `data_gen.inference_config`).
"""

from __future__ import annotations

import logging
import re
import textwrap
from dataclasses import dataclass

import litellm

from data_gen.question_sampler import SampledEntry
from data_gen.weave_logger import weave_op

logger = logging.getLogger(__name__)

_TASK_TRUTH_SYSTEM_TEMPLATE = """\
You are an expert at creating {domain_label} tasks for AI agent training.

The task must center on this primitive skill:

Skill type: {skill_type_name}
Primitive: {primitive_description}
Goal: {goal}
Expected operations:
{expected_operations}
Constraints:
{constraints}
Likely tools: {likely_tools}

Universal Task Requirements:
- Challenging to solve: Requires domain knowledge, analytical thinking, and \
efficient implementation.
- Easy to verify: Success must be determinable by programmatically checking \
outputs, exit codes, or system state.
- Self-contained: All necessary information must be in the prompt.
- Realistic: The problem should resemble tasks professionals face in this domain.

Respond in XML format using these tags:

<task>
        A detailed task description written as a user would ask an AI assistant.
        Give the names of the precise contents of files, ports, directories, etc.
        This should be a very detailed description of the final state of the system.
        For example, if you are asking the agent to create a log file, you should
        precisely specify the format it should be in so that an automated test can
        verify it.
        Ask the agent to create a log file whenever some verification is required.
        You only have about 1000-1500 words to work with. So balance between
        conciseness and detail.
        DO NOT directly give the commands to the agent.
</task>

<truth>
        Insert *privileged* ground-truth data that automated test suites will
        rely on to verify correct task execution.
        These values **must NOT** appear in the public task description.

        Be very detailed here. Give the names / placeholders of the precise
        contents of files, ports, directories, repositories, websites etc.
        Any processes, files, directories that should be created before the task
        starts should be mentioned here.
        Any files that should be created by the agent and their contents should
        be mentioned here.

        Ground-truth principles (for accurate automated verification):
        * **Consistency:** Anything in *truth* that could be computed from the setup
          code, random seeds, or the task rules must actually follow from them. Do not
          assert derived numbers, digests, or file bodies unless they are implied by
          what you specified - avoid plausible-looking literals produced without that chain.
        * **Reproducibility:** Prefer stating *how* to obtain a golden value (procedure,
          formula, or a short **runnable** snippet that prints the canonical result) over
          pasting opaque constants that nothing in the pipeline verifies.
        * **Causal ordering:** When setup involves multiple steps (random draws, mutations,
          I/O), make the sequence explicit. Headline summaries (e.g. simple counts) must
          reflect the real order of operations, not an informal intuition.
        * **Single source of truth:** Setup scripts, narrative expectations, and any
          "expected output" blocks must agree; resolve contradictions before finishing.
</truth>

Critical Rules:
* No Leakage: Never include code that solves the task in the <task> description.
* Verification: Prioritize tasks with clear, programmatic verification.
* Originality: Tasks should require thought, not just copying standard tutorials.
* Complete Specification: Include all information needed to complete the task \
(file paths, formats, constraints).
* Place any secret, ground-truth verification data exclusively under <truth>.
* The agent will not have root access. Make sure the right permissions are set \
for files and directories.
* When you mention a file or directory, write the full path (not relative).
* We will be using Docker to run the agent. Make sure the task is valid when \
the container is built.
* Don't create tasks that require having the latest information.
* The home path is /home/user.
* Don't create tasks the setup of which will require su access.
* The task is multi-turn, so the agent will interact in a terminal to finish \
the task.
* Don't discourage the agent from using console output to finish the task.
* Do not constrain the number of commands the agent may use."""

_TASK_TRUTH_USER_TEMPLATE = """\
Generate one task for the domain "{domain_name}" ({domain_description}).

- Persona: {persona_role} - {persona_description}
- Language/runtime: {language_name} ({language_runtime})
- Package manager: {package_manager}
- Build command: {build_command}
- Test command: {test_command}

The task should:
1. Be framed from the persona's perspective.
2. Center on the primitive skill described in the system prompt.
3. Be challenging to solve but easy to verify.
{context_block}"""

_CONTEXT_BLOCK_TEMPLATE = """
Avoid generating a task that duplicates or closely resembles any of these \
already-generated tasks:
{items}"""

_TEST_SYSTEM_MSG = """\
You are a senior Python engineer who writes robust pytest suites.
Write a robust pytest suite that validates the **FINAL** state of the operating-system / container **after** the student has
completed the task described.
Use the privileged *truth* data to assert the exact expected end state for the task to be completed.

Rules:
* The filename must be ``test_final_state.py`` (show it in a header comment).
* Use **only** the Python standard library and ``pytest`` (no third-party libs).
* Failures must clearly explain **what is still wrong**.
* When you check for files or directories, always use their *absolute* paths exactly as given (no relative paths).
* Ensure that the state of the OS matches the truth after the task is completed.
* Write the code in a fenced code block that can be parsed to get a single python file.

Ground-truth alignment (principled tests):
* Treat *truth* as the **intent** of the rubric, not as guaranteed-correct literals. When
  the task and setup logically determine an expected value, **derive or recompute** it in
  test code (stdlib only) instead of copying opaque constants from *truth* without checking.
* Match the **same procedures and ordering** as the described setup and task when you
  assert counts, checksums, or structured outputs - so tests stay faithful to the spec.
* Use the **strongest appropriate** assertion: prefer invariants, structure, and
  reproducible computations over brittle full-file equality when *truth* still allows the
  task to be graded fairly.
"""

_TEST_USER_TEMPLATE = """\
The task description is: {task_description}
The truth value is: {truth}
Write the code in a fenced code block that can be parsed."""


@dataclass(frozen=True)
class GeneratedQuestion:
    """The full spec for one generated question, pre-Harbor-materialization."""

    sample: SampledEntry
    task_description: str
    truth: str
    test_code: str
    model: str


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def _build_task_truth_messages(sample: SampledEntry, context: list[str]) -> list[dict[str, str]]:
    guidance = sample.primitive.guidance
    system = _TASK_TRUTH_SYSTEM_TEMPLATE.format(
        domain_label=sample.domain.name,
        skill_type_name=sample.skill_type.name,
        primitive_description=sample.primitive.description,
        goal=guidance.goal if guidance else sample.primitive.description,
        expected_operations=_format_bullets(guidance.expected_operations if guidance else []),
        constraints=_format_bullets(guidance.constraints if guidance else []),
        likely_tools=", ".join(guidance.likely_tools) if guidance and guidance.likely_tools else "(unspecified)",
    )

    context_block = _CONTEXT_BLOCK_TEMPLATE.format(items=_format_bullets(context)) if context else ""
    user = _TASK_TRUTH_USER_TEMPLATE.format(
        domain_name=sample.domain.name,
        domain_description=sample.domain.description,
        persona_role=sample.persona.role,
        persona_description=sample.persona.description,
        language_name=sample.language.name,
        language_runtime=sample.language.runtime,
        package_manager=sample.language.package_manager,
        build_command=sample.language.build_command,
        test_command=sample.language.test_command,
        context_block=context_block,
    )
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _parse_task_truth(raw: str) -> tuple[str, str]:
    task_match = re.search(r"<task>(.*?)</task>", raw, re.DOTALL)
    truth_match = re.search(r"<truth>(.*?)</truth>", raw, re.DOTALL)
    if not task_match or not task_match.group(1).strip():
        raise ValueError(f"No <task> block found in generation response:\n{raw}")
    if not truth_match or not truth_match.group(1).strip():
        raise ValueError(f"No <truth> block found in generation response:\n{raw}")
    return task_match.group(1).strip(), truth_match.group(1).strip()


def _parse_test_code(raw: str) -> str:
    fence_match = re.search(r"```(?:python)?\n(.*?)```", raw, re.DOTALL | re.IGNORECASE)
    code = fence_match.group(1) if fence_match else raw
    code = textwrap.dedent(code).rstrip()
    compile(code, "test_final_state.py", "exec")  # raises SyntaxError if malformed
    return code


def _retry(fn, max_retries: int, description: str):
    """Calls `fn()`, retrying on ValueError/SyntaxError up to `max_retries` times.

    Weaker models occasionally truncate or malform structured output (e.g.
    never closing `</truth>`, or emitting invalid Python) - same class of
    unreliability tmax's own legacy pipeline retries against
    (`apptainer_def_gen.iterate_def_template_batch`). Re-sampling usually
    produces a well-formed response since the failure isn't deterministic.
    """
    last_error: Exception | None = None
    for attempt in range(1 + max_retries):
        try:
            return fn()
        except (ValueError, SyntaxError) as e:
            last_error = e
            logger.warning("%s failed (attempt %d/%d): %s", description, attempt + 1, 1 + max_retries, e)
    raise last_error


@weave_op
def generate_question(
    sample: SampledEntry,
    model: str,
    context: list[str] | None = None,
    temperature: float = 1.0,
    max_tokens: int = 8192,
    extra_kwargs: dict[str, object] | None = None,
    max_retries: int = 2,
) -> GeneratedQuestion:
    """Generates one full-spec question for `sample` via two LLM calls.

    Args:
        sample: The catalog entry (domain/skill type/primitive/persona/
            language) to build the question around.
        model: LiteLLM model string (e.g. "anthropic/claude-sonnet-4-5", or
            "openai/<model_id>" when routed through an OpenAI-compatible
            endpoint via `extra_kwargs`).
        context: Previously generated task descriptions, so the model
            avoids repeating them. Empty/None for the first question.
        temperature: Sampling temperature for the task+truth call.
        max_tokens: Max tokens for each call.
        extra_kwargs: Extra kwargs merged into every `litellm.completion`
            call (e.g. `api_base`/`api_key`/`extra_headers` for a
            self-hosted or alternate OpenAI-compatible provider).
        max_retries: Re-sample attempts if a response fails to parse (see `_retry`).

    Returns:
        The parsed GeneratedQuestion, ready for Harbor materialization.
    """
    extra_kwargs = extra_kwargs or {}

    def _call_task_truth() -> tuple[str, str]:
        response = litellm.completion(
            model=model,
            messages=_build_task_truth_messages(sample, context or []),
            temperature=temperature,
            max_tokens=max_tokens,
            **extra_kwargs,
        )
        return _parse_task_truth(response.choices[0].message.content)

    task_description, truth = _retry(_call_task_truth, max_retries, "task+truth generation")

    def _call_test() -> str:
        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": _TEST_SYSTEM_MSG},
                {
                    "role": "user",
                    "content": _TEST_USER_TEMPLATE.format(task_description=task_description, truth=truth),
                },
            ],
            temperature=0.6,
            max_tokens=max_tokens,
            **extra_kwargs,
        )
        return _parse_test_code(response.choices[0].message.content)

    test_code = _retry(_call_test, max_retries, "test generation")

    return GeneratedQuestion(
        sample=sample, task_description=task_description, truth=truth, test_code=test_code, model=model
    )
