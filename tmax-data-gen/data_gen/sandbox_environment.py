"""Executes bash commands inside a W&B/CoreWeave Sandbox (the `cwsandbox` client -
see https://docs.wandb.ai/sandboxes; `wandb.sandbox` is a deprecated wrapper
around the same client and is not used here).

Matches the same interface as mini-swe-agent's built-in environments (see
`minisweagent.environments.docker.DockerEnvironment`): `.execute(action, cwd,
timeout) -> {"output", "returncode", "exception_info"}`. This is what lets
`data_gen.harness.build_agent(..., environment="sandbox", ...)` plug in with
no other changes to the agent loop.

Sandboxes only pull public pre-built images (no Dockerfile build support), so
`container_image` should be a plain public image reference - see
`data_gen.harbor.resolve_base_image` for the per-language default used
elsewhere in this project.

Owns the sandbox's lifecycle (creates + starts it, stops it on cleanup)
unless an already-running `sandbox=` is passed in - e.g. so a rollout driver
can create one sandbox, run the agent in it, and then run the task's
verifier in that same sandbox afterward (see `data_gen.rollout`).
"""

from __future__ import annotations

import logging
from typing import Any

import cwsandbox
from pydantic import BaseModel, ConfigDict

from minisweagent.exceptions import Submitted
from minisweagent.utils.serialize import recursive_merge

from data_gen.browser_setup import setup_browser
from data_gen.env_exec import query_platform_info

logger = logging.getLogger("minisweagent.environment")


class SandboxEnvironmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    container_image: str = "python:3.11"
    """Public container image to start. Ignored when `sandbox` is given."""
    cwd: str = "/"
    """Working directory in which to execute commands."""
    environment_variables: dict[str, str] = {}
    """Environment variables for the sandbox (sandbox-wide, set at creation -
    cwsandbox's exec() has no per-call env override). Ignored when `sandbox`
    is given."""
    timeout: int = 60
    """Default timeout in seconds for executing a command."""
    max_lifetime_seconds: float = 3600.0
    """Max sandbox lifetime (server-side). Ignored when `sandbox` is given."""
    sandbox: cwsandbox.Sandbox | None = None
    """An already-running Sandbox to reuse instead of creating a new one.
    When given, this environment does not stop it on cleanup - the caller
    that created it owns its lifecycle."""
    enable_browser: bool = False
    """Installs Playwright + headless Chromium and starts
    `data_gen.browser_driver` in the sandbox, so the agent can drive a
    browser with `curl localhost:8765/{goto,screenshot,click,scroll}` bash
    commands (see `data_gen.browser_setup`). Ignored when `sandbox` is
    given - set it up once yourself and reuse that sandbox instead."""


class SandboxEnvironment:
    def __init__(self, *, config_class: type = SandboxEnvironmentConfig, **kwargs):
        self.config = config_class(**kwargs)
        self._owns_sandbox = self.config.sandbox is None
        if self.config.sandbox is not None:
            self.sandbox = self.config.sandbox
        else:
            self.sandbox = cwsandbox.Sandbox.run(
                "sleep",
                "infinity",
                container_image=self.config.container_image,
                auth=cwsandbox.AuthStrategy.WANDB,
                environment_variables=self.config.environment_variables,
                max_lifetime_seconds=self.config.max_lifetime_seconds,
            ).wait()
            if self.config.enable_browser:
                setup_browser(self._raw_exec)
        self._platform_info = query_platform_info(self)

    def _raw_exec(self, command: str) -> None:
        """Runs a setup command in the sandbox, raising on failure.

        Unlike `execute()`, this is not part of the agent-facing action
        contract - it's only used at construction time by `setup_browser`.
        """
        process = self.sandbox.exec(["bash", "-lc", command], cwd="/", timeout_seconds=300)
        result = process.result()
        if result.returncode != 0:
            raise RuntimeError(f"Browser setup command failed ({result.returncode}): {command}\n{result.stdout}{result.stderr}")

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        """Executes a command in the sandbox and returns the result as a dict."""
        command = action.get("command", "")
        cwd = cwd or self.config.cwd
        try:
            process = self.sandbox.exec(["bash", "-lc", command], cwd=cwd, timeout_seconds=timeout or self.config.timeout)
            result = process.result()
            output = {"output": result.stdout + result.stderr, "returncode": result.returncode, "exception_info": ""}
        except Exception as e:
            output = {
                "output": "",
                "returncode": -1,
                "exception_info": f"An error occurred while executing the command: {e}",
                "extra": {"exception_type": type(e).__name__, "exception": str(e)},
            }
        self._check_finished(output)
        return output

    def _check_finished(self, output: dict):
        """Raises Submitted if the output indicates task completion."""
        lines = output.get("output", "").lstrip().splitlines(keepends=True)
        if lines and lines[0].strip() == "COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT" and output["returncode"] == 0:
            submission = "".join(lines[1:])
            raise Submitted(
                {
                    "role": "exit",
                    "content": submission,
                    "extra": {"exit_status": "Submitted", "submission": submission},
                }
            )

    def get_template_vars(self, **kwargs) -> dict[str, Any]:
        return recursive_merge(self.config.model_dump(exclude={"sandbox"}), self._platform_info, kwargs)

    def serialize(self) -> dict:
        return {
            "info": {
                "config": {
                    "environment": self.config.model_dump(mode="json", exclude={"sandbox"}),
                    "environment_type": f"{self.__class__.__module__}.{self.__class__.__name__}",
                }
            }
        }

    def cleanup(self):
        """Stops the sandbox, unless it was passed in already-running (not owned).

        Idempotent: `__del__` calls this again at garbage collection even
        after an explicit `cleanup()` already ran, and by then Python's own
        modules (including logging) may be partially torn down - so a
        second call must be a clean no-op, not attempt another stop.
        """
        if self._owns_sandbox and getattr(self, "sandbox", None) is not None:
            try:
                self.sandbox.stop(missing_ok=True)
            except Exception:
                logger.warning("Failed to stop sandbox", exc_info=True)
            finally:
                self.sandbox = None

    def __del__(self):
        self.cleanup()
