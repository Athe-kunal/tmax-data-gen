"""Shared setup for the optional in-sandbox browser (screenshot/click/scroll).

Used by both `data_gen.sandbox_environment.SandboxEnvironment` and
`data_gen.daytona_environment.DaytonaEnvironment` when constructed with
`enable_browser=True`. Installs Playwright + headless Chromium, writes
`data_gen.browser_driver` into the sandbox, and starts it in the background
on `BROWSER_DRIVER_PORT`. After this returns, the agent (or a human writing
a task's system prompt) drives the browser with plain `curl` bash commands:

    curl -s -X POST localhost:8765/goto -d '{"url": "https://example.com"}'
    curl -s -X POST localhost:8765/screenshot
    curl -s -X POST localhost:8765/click -d '{"x": 100, "y": 200}'
    curl -s -X POST localhost:8765/scroll -d '{"dx": 0, "dy": 300}'

No changes to the environment's `.execute()` contract are needed - this is
plumbing that runs once at construction time, not a new action type.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from minisweagent.models.utils.openai_multimodal import DEFAULT_MULTIMODAL_REGEX

BROWSER_DRIVER_PORT = 8765

_DRIVER_SOURCE = (Path(__file__).parent / "browser_driver.py").read_text()

__all__ = ["BROWSER_DRIVER_PORT", "DEFAULT_MULTIMODAL_REGEX", "setup_browser"]

# DEFAULT_MULTIMODAL_REGEX (re-exported above) matches the
# <MSWEA_MULTIMODAL_CONTENT> tags that /screenshot emits - pass it as
# model_kwargs={"multimodal_regex": ...} (or let
# data_gen.harness.build_agent default it, see there) so the model sees an
# actual image content block instead of raw tagged text.


def setup_browser(exec_fn: Callable[[str], None], *, timeout: int = 300) -> None:
    """Installs and starts the browser driver in a sandbox via `exec_fn`.

    Args:
        exec_fn: Runs a single bash command in the sandbox and raises on
            nonzero exit / timeout (e.g. a thin wrapper around the
            sandbox's own low-level exec, not `.execute()` - failures here
            should surface as constructor errors, not as agent turns).
        timeout: Seconds to allow for the (slow, one-time) Chromium
            download/install.
    """
    write_driver = (
        "cat > /opt/browser_driver.py << 'BROWSER_DRIVER_EOF'\n"
        f"{_DRIVER_SOURCE}\n"
        "BROWSER_DRIVER_EOF"
    )
    exec_fn(write_driver)
    exec_fn("pip install --quiet playwright && python3 -m playwright install --with-deps chromium")
    exec_fn("nohup python3 /opt/browser_driver.py > /tmp/browser_driver.log 2>&1 & disown")
    exec_fn(
        "for i in $(seq 1 60); do "
        f"curl -sf localhost:{BROWSER_DRIVER_PORT}/health && exit 0; sleep 1; "
        "done; echo 'browser driver failed to start' >&2; cat /tmp/browser_driver.log >&2; exit 1"
    )
