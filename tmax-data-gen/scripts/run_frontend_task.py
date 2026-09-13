"""One-off, hand-authored frontend-engineering task, run through the same
solve+verify+Weave-logging pipeline as the KG-generated tasks, since the
artifact catalog has no frontend/UI domain or skill to sample/retrieve from
(confirmed: no javascript/typescript language entry, no DOM/CSS/browser
primitive in any domain's skills.yaml).

Runs in a W&B/CoreWeave Sandbox with the in-sandbox browser enabled
(Playwright + headless Chromium - see data_gen.browser_setup), and traces
the whole run to Weave via @weave_op, matching data_gen.harness.run_agent's
and data_gen.multi_turn_rollout.run_multi_turn_rollout's pattern.

Task: a small vanilla HTML/JS counter widget has a bug in its click handler
(increments by 2 instead of 1, and the second click doesn't update the DOM
until a third click due to a stale-closure bug). The agent must fix
script.js so the on-page counter behaves correctly. Verified by an actual
headless-browser interaction (not a text/string check).
"""

from __future__ import annotations

import base64
import textwrap
import uuid
from pathlib import Path

from data_gen.catalog import Language, SkillType, Primitive, load_catalog
from data_gen.env_exec import read_file as _read_file
from data_gen.env_exec import run as _run
from data_gen.env_exec import write_file as _write_file
from data_gen.gold import is_gold, materialize_gold_turn
from data_gen.harbor import TEST_SH
from data_gen.harness import build_agent
from data_gen.inference_config import OpenAICompatibleConfig
from data_gen.multi_turn_rollout import TurnResult
from data_gen.question_gen import GeneratedQuestion
from data_gen.question_sampler import SampledEntry
from data_gen.browser_setup import setup_browser
from data_gen.sandbox_environment import SandboxEnvironment
from data_gen.weave_logger import weave_op

_WORKDIR = "/home/user/app"
_TESTS_DIR = "/tests"
_CONTAINER_IMAGE = "python:3.11-slim"  # has python3/pip already, for both pytest and playwright

# curl is needed by browser_setup.setup_browser's own health check - not
# present in python:3.11-slim, and SandboxEnvironment(enable_browser=True)
# runs setup_browser() synchronously inside __init__, before any code here
# gets a chance to apt-get install anything first (confirmed live: "curl:
# command not found" x60, health check timed out). So this environment is
# built in two steps instead of one: create the sandbox WITHOUT
# enable_browser, install curl/python3/pytest ourselves, then call
# setup_browser() manually (see run_frontend_task) once curl exists.
_INSTALL_DEPS_CMD = (
    "apt-get update && apt-get install -y --no-install-recommends python3 python3-pip curl "
    "&& (python3 -m pip install --no-cache-dir --break-system-packages pytest "
    "|| python3 -m pip install --no-cache-dir pytest)"
)

_INDEX_HTML = """\
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Counter</title></head>
<body>
  <h1>Click Counter</h1>
  <p>Count: <span id="count">0</span></p>
  <button id="increment">+1</button>
  <script src="script.js"></script>
</body>
</html>
"""

# Buggy: (1) increments by 2 instead of 1, (2) reads `count` into a local
# before incrementing it, then writes the *old* value back to the DOM (an
# off-by-one-click stale-read bug) - a real frontend debugging task, not a
# trivial typo.
_SCRIPT_JS_BUGGY = """\
let count = 0;

document.getElementById("increment").addEventListener("click", function () {
  const display = document.getElementById("count");
  const shown = display.textContent;
  count += 2;
  display.textContent = shown;
  display.textContent = String(count - 1);
});
"""

_SETUP_SCRIPT = f"""\
mkdir -p {_WORKDIR}
cat > {_WORKDIR}/index.html << 'HTML_EOF'
{_INDEX_HTML}
HTML_EOF
cat > {_WORKDIR}/script.js << 'JS_EOF'
{_SCRIPT_JS_BUGGY}
JS_EOF
"""

_TASK_DESCRIPTION = textwrap.dedent(f"""\
    You're a web developer building a feature. There's a small counter widget
    at {_WORKDIR}/index.html (+ {_WORKDIR}/script.js) with a bug report: "the
    on-page count doesn't match how many times I clicked the button."

    Fix {_WORKDIR}/script.js so that after N clicks of the "+1" button, the
    `#count` element's text is exactly the string `N` (starting from `0`
    before any clicks). Do not change index.html's structure/ids.

    `playwright` (Python) is already installed. To check your fix without
    guessing, you can run a quick headless-browser check as plain text output
    (no screenshots - this endpoint's model can't accept image content), e.g.:
        python3 -c "
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        page = p.chromium.launch().new_page()
        page.goto('file://{_WORKDIR}/index.html')
        b = page.locator('#increment')
        for _ in range(3):
            b.click()
        print(page.locator('#count').inner_text())
    "
    That should print exactly "3". Use it (or just read/reason about the JS)
    to verify your fix before finishing.
""")

_TRUTH = (
    "script.js's click handler must increment `count` by exactly 1 per "
    "click and write the *new* value of `count` to #count.textContent - not "
    "2, and not a value read before the increment."
)

_TEST_CODE = textwrap.dedent("""\
    import pathlib

    from playwright.sync_api import sync_playwright

    HTML_PATH = "/home/user/app/index.html"
    SCREENSHOT_DIR = pathlib.Path("/logs/verifier/screenshots")


    def test_counter_increments_by_one_and_updates_immediately():
        SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(f"file://{HTML_PATH}")

            page.screenshot(path=str(SCREENSHOT_DIR / "click_0.png"))
            assert page.locator("#count").inner_text() == "0"

            button = page.locator("#increment")
            for i, expected in enumerate(("1", "2", "3"), start=1):
                button.click()
                page.screenshot(path=str(SCREENSHOT_DIR / f"click_{i}.png"))
                actual = page.locator("#count").inner_text()
                assert actual == expected, f"after click {i}, expected #count={expected!r}, got {actual!r}"

            browser.close()
""")


def _pull_dir(env, remote_dir: str, local_dir: Path) -> list[Path]:
    """Downloads every file in `remote_dir` (flat, no subdirs) to `local_dir`.

    `env_exec.read_file` is text-only (`cat`) - not safe for PNGs - so this
    round-trips each file through base64, same encoding `env_exec.write_file`
    already uses for the opposite direction.
    """
    local_dir.mkdir(parents=True, exist_ok=True)
    names = _run(env, f"ls -1 {remote_dir}")["output"].split()
    paths = []
    for name in names:
        b64 = _run(env, f"base64 -w0 {remote_dir}/{name}")["output"].strip()
        local_path = local_dir / name
        local_path.write_bytes(base64.b64decode(b64))
        paths.append(local_path)
    return paths


def _build_sample() -> SampledEntry:
    """Reuses the real `software_engineering` domain + its actual
    "web developer building a feature" persona from the catalog (both are
    real taxonomy content), paired with a hand-authored skill_type/primitive
    and a synthetic Language - since no frontend primitive or JS/TS language
    entry exists in artifacts/ to draw from instead."""
    catalog = load_catalog(
        Path(__file__).resolve().parent.parent / "artifacts"
    )
    bundle = next(b for b in catalog.domains if b.domain.id == "software_engineering")
    persona = next(p for p in bundle.personas.personas if p.id == "web-developer-building-a-feature")

    skill_type = SkillType(
        id="frontend-hand-authored",
        name="Frontend (hand-authored)",
        primitives=[
            Primitive(
                id="dom-event-handler-bugfix",
                description="Fix a stale-state/off-by-N bug in a DOM click handler",
            )
        ],
    )
    language = Language(
        schema_version=1,
        id="javascript",
        name="JavaScript",
        sampling_weight=0.0,
        runtime="browser",
        runtime_guidance_origin="hand-authored",
        package_manager="none",
        build_command="",
        test_command="",
        compatible_domain_ids=["software_engineering"],
        base_image=_CONTAINER_IMAGE,
    )
    return SampledEntry(
        domain=bundle.domain,
        skill_type=skill_type,
        primitive=skill_type.primitives[0],
        persona=persona,
        language=language,
    )


@weave_op
def run_frontend_task(solve_model: str, model_style: str = "text", screenshots_dir: Path | None = None) -> TurnResult:
    """Runs the hand-authored frontend task end-to-end in a W&B Sandbox with
    the browser enabled, verifies it, and returns the TurnResult (traced to
    Weave as the root op).

    Args:
        screenshots_dir: If given, the verifier's per-click screenshots
            (see `_TEST_CODE` - it screenshots before and after each click,
            not just the final state) are pulled from the sandbox into this
            local directory before it's torn down.
    """
    inference_config = OpenAICompatibleConfig.from_env(model=solve_model)
    litellm_model, model_kwargs = inference_config.litellm_model(), inference_config.litellm_kwargs()

    sample = _build_sample()
    question = GeneratedQuestion(
        sample=sample,
        task_description=_TASK_DESCRIPTION,
        truth=_TRUTH,
        test_code=_TEST_CODE,
        model="hand-authored",
        setup_script=_SETUP_SCRIPT,
    )

    env = SandboxEnvironment(container_image=_CONTAINER_IMAGE)
    try:
        _run(env, _INSTALL_DEPS_CMD, timeout=300)
        setup_browser(env._raw_exec, timeout=300)  # installs playwright + chromium, starts the driver
        _run(env, question.setup_script, timeout=120)

        agent = build_agent(
            litellm_model,
            environment="sandbox",
            # enable_browser deliberately omitted here: it would set
            # multimodal_regex, converting any /screenshot output into an
            # image content block - but this backend (DeepSeek-V4-Flash-0731
            # via W&B Inference) rejects multimodal input outright
            # ("Received multimodal data but multimodal processing is not
            # enabled" - confirmed live). Verification stays text-only (see
            # _TASK_DESCRIPTION's playwright snippet), so this isn't needed.
            environment_kwargs={"sandbox": env.sandbox, "cwd": _WORKDIR},
            agent_config={"step_limit": 60, "cost_limit": 3.0},
            model_kwargs=model_kwargs,
            model_style=model_style,
        )
        agent_exit = agent.run(question.task_description)
        turn_messages = list(agent.messages)

        _write_file(env, f"{_TESTS_DIR}/test.sh", TEST_SH.encode())
        _write_file(env, f"{_TESTS_DIR}/test_final_state.py", question.test_code.encode())
        _run(env, f"bash {_TESTS_DIR}/test.sh")
        reward = float(_read_file(env, "/logs/verifier/reward.txt").strip())
        verifier_stdout = _read_file(env, "/logs/verifier/test-stdout.txt")
        if screenshots_dir is not None:
            _pull_dir(env, "/logs/verifier/screenshots", screenshots_dir)
    finally:
        env.cleanup()

    return TurnResult(
        sample=sample,
        question=question,
        messages=turn_messages,
        reward=reward,
        verifier_stdout=verifier_stdout,
        agent_exit=agent_exit,
    )


if __name__ == "__main__":
    import argparse
    import shutil
    import tempfile

    parser = argparse.ArgumentParser()
    parser.add_argument("--solve-model", default="deepseek-ai/DeepSeek-V4-Flash-0731")
    parser.add_argument("--model-style", choices=("text", "toolcall"), default="text")
    parser.add_argument("--out-dir", type=Path, default=Path("gold_tasks"))
    parser.add_argument("--n", type=int, default=1)
    args = parser.parse_args()

    for i in range(args.n):
        print(f"=== frontend task run {i + 1}/{args.n} ===")
        with tempfile.TemporaryDirectory() as staging:
            turn = run_frontend_task(args.solve_model, args.model_style, screenshots_dir=Path(staging))
            print(f"reward={turn.reward}")
            print(turn.verifier_stdout[-2000:])
            if is_gold(turn):
                task_name = f"frontend-dom-event-handler-bugfix-{uuid.uuid4().hex[:8]}"
                path = materialize_gold_turn(turn, args.out_dir / task_name)
                shutil.copytree(staging, path / "screenshots")
                print(f"GOLD -> {path} (+ {len(list((path / 'screenshots').iterdir()))} verifier screenshots)")
            else:
                print("NOT gold (reward < 1.0) - not materialized into gold_tasks/")
