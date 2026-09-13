"""Executes bash commands inside a Daytona sandbox (https://www.daytona.io/docs/).

Matches the same interface as mini-swe-agent's built-in environments (see
`minisweagent.environments.docker.DockerEnvironment`), so
`data_gen.harness.build_agent(..., environment="daytona", ...)` plugs in with
no other changes to the agent loop. Structurally a near-mirror of
`data_gen.sandbox_environment.SandboxEnvironment` (the W&B/CoreWeave
backend) - same contract, different SDK underneath - which is what makes
`data_gen.rollout` work against either without caring which one it's given.

Auth: `DaytonaConfig()` reads `DAYTONA_API_KEY` from the environment if no
`api_key` is passed explicitly - no per-organization approval gate, unlike
W&B Sandboxes' public-preview access model.
"""

from __future__ import annotations

import logging
from typing import Any

from daytona import CreateSandboxFromImageParams, Daytona, DaytonaConfig, Sandbox
from pydantic import BaseModel, ConfigDict

from minisweagent.exceptions import Submitted
from minisweagent.utils.serialize import recursive_merge

from data_gen.browser_setup import setup_browser
from data_gen.env_exec import query_platform_info

logger = logging.getLogger("minisweagent.environment")


class DaytonaEnvironmentConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    image: str = "python:3.11"
    """Public container image to start. Ignored when `sandbox` is given."""
    cwd: str = "/"
    """Working directory in which to execute commands."""
    env: dict[str, str] = {}
    """Environment variables for the sandbox. Ignored when `sandbox` is given."""
    timeout: int = 60
    """Default timeout in seconds for executing a command."""
    sandbox: Sandbox | None = None
    """An already-running Sandbox to reuse instead of creating a new one.
    When given, this environment does not delete it on cleanup - the caller
    that created it owns its lifecycle."""
    enable_browser: bool = False
    """Installs Playwright + headless Chromium and starts
    `data_gen.browser_driver` in the sandbox, so the agent can drive a
    browser with `curl localhost:8765/{goto,screenshot,click,scroll}` bash
    commands (see `data_gen.browser_setup`). Ignored when `sandbox` is
    given - set it up once yourself and reuse that sandbox instead."""


class DaytonaEnvironment:
    def __init__(self, *, config_class: type = DaytonaEnvironmentConfig, **kwargs):
        self.config = config_class(**kwargs)
        self._owns_sandbox = self.config.sandbox is None
        if self.config.sandbox is not None:
            self.sandbox = self.config.sandbox
        else:
            self._client = Daytona(DaytonaConfig())
            self.sandbox = self._client.create(
                CreateSandboxFromImageParams(image=self.config.image, env_vars=self.config.env)
            )
            if self.config.enable_browser:
                setup_browser(self._raw_exec)
        self._platform_info = query_platform_info(self)

    def _raw_exec(self, command: str) -> None:
        """Runs a setup command in the sandbox, raising on failure.

        Unlike `execute()`, this is not part of the agent-facing action
        contract - it's only used at construction time by `setup_browser`.
        """
        response = self.sandbox.process.exec(command, cwd="/", timeout=300)
        if response.exit_code != 0:
            raise RuntimeError(f"Browser setup command failed ({response.exit_code}): {command}\n{response.result}")

    def execute(self, action: dict, cwd: str = "", *, timeout: int | None = None) -> dict[str, Any]:
        """Executes a command in the sandbox and returns the result as a dict."""
        command = action.get("command", "")
        cwd = cwd or self.config.cwd
        try:
            response = self.sandbox.process.exec(command, cwd=cwd, timeout=timeout or self.config.timeout)
            output = {"output": response.result, "returncode": response.exit_code, "exception_info": ""}
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
        """Deletes the sandbox, unless it was passed in already-running (not owned).

        Idempotent: `__del__` calls this again at garbage collection even
        after an explicit `cleanup()` already ran, and by then Python's own
        modules (including logging) may be partially torn down - so a
        second call must be a clean no-op, not attempt another delete.
        """
        if self._owns_sandbox and getattr(self, "sandbox", None) is not None:
            try:
                self.sandbox.delete()
            except Exception:
                logger.warning("Failed to delete sandbox", exc_info=True)
            finally:
                self.sandbox = None

    def __del__(self):
        self.cleanup()
