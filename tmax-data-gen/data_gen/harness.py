"""Thin wrapper around mini-swe-agent for programmatic use in data_gen.

This module exposes a single entry point, `run_agent`, that builds a
mini-swe-agent `DefaultAgent` (model + environment + config) and runs it
against a task string, without going through the `mini` CLI.

See https://mini-swe-agent.com for the underlying project.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

import yaml
from minisweagent import package_dir
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.litellm_model import LitellmModel

from data_gen.daytona_environment import DaytonaEnvironment
from data_gen.sandbox_environment import SandboxEnvironment
from data_gen.weave_logger import weave_op

_DEFAULT_CONFIG_PATH = package_dir / "config" / "default.yaml"

_ENVIRONMENTS = {
    "local": LocalEnvironment,
    "docker": DockerEnvironment,
    "sandbox": SandboxEnvironment,
    "daytona": DaytonaEnvironment,
}


def load_default_agent_config(config_path: Path = _DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Loads the `agent:` section of a mini-swe-agent YAML config.

    Args:
        config_path: Path to a mini-swe-agent config file. Defaults to the
            config bundled with the mini-swe-agent package.

    Returns:
        The `agent` mapping from the config file (system/instance templates,
        step_limit, cost_limit, etc.).
    """
    return yaml.safe_load(config_path.read_text())["agent"]


def build_agent(
    model_name: str,
    environment: Literal["local", "docker", "sandbox", "daytona"] = "local",
    environment_kwargs: dict[str, Any] | None = None,
    agent_config: dict[str, Any] | None = None,
    model_kwargs: dict[str, Any] | None = None,
) -> DefaultAgent:
    """Builds a mini-swe-agent `DefaultAgent` ready to `.run(task)`.

    Args:
        model_name: LiteLLM model name (e.g. "gemini/gemini-3.1-pro-preview",
            or "openai/<model_id>" when routed through an OpenAI-compatible
            endpoint via `model_kwargs`).
        environment: Which mini-swe-agent environment backend to execute
            actions in. "local" runs bash commands directly on this
            machine; "docker" runs them inside a local container; "sandbox"
            runs them inside a W&B/CoreWeave Sandbox (see
            data_gen.sandbox_environment.SandboxEnvironment); "daytona" runs
            them inside a Daytona sandbox (see
            data_gen.daytona_environment.DaytonaEnvironment).
        environment_kwargs: Extra kwargs forwarded to the environment's
            constructor (e.g. `{"image": "python:3.13"}` for docker, or
            `{"sandbox": <existing sandbox object>}` to reuse an
            already-running "sandbox"/"daytona" sandbox instead of starting
            a new one).
        agent_config: Overrides for the agent config (system_template,
            instance_template, step_limit, cost_limit, ...). Merged over the
            defaults bundled with mini-swe-agent.
        model_kwargs: Extra kwargs merged into every underlying
            `litellm.completion` call the model makes (e.g. `api_base`/
            `api_key`/`extra_headers` for a self-hosted or alternate
            OpenAI-compatible provider - see
            `data_gen.inference_config.OpenAICompatibleConfig.litellm_kwargs`).

    Returns:
        A `DefaultAgent` instance, not yet run.
    """
    if environment not in _ENVIRONMENTS:
        raise ValueError(f"Unknown environment {environment!r}, expected one of {list(_ENVIRONMENTS)}")

    env = _ENVIRONMENTS[environment](**(environment_kwargs or {}))
    # ignore_errors: litellm has no pricing entry for most self-hosted/custom
    # OpenAI-compatible models (e.g. Weave Inference's), so cost tracking
    # would otherwise raise on every single completion call.
    model = LitellmModel(model_name=model_name, model_kwargs=model_kwargs or {}, cost_tracking="ignore_errors")
    config = load_default_agent_config() | (agent_config or {})
    return DefaultAgent(model, env, **config)


@weave_op
def run_agent(
    task: str,
    model_name: str,
    environment: Literal["local", "docker", "sandbox", "daytona"] = "local",
    environment_kwargs: dict[str, Any] | None = None,
    agent_config: dict[str, Any] | None = None,
    model_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Builds an agent and runs it against a single task.

    Args:
        task: The task/problem statement to solve.
        model_name: LiteLLM model name.
        environment: "local", "docker", "sandbox", or "daytona". See `build_agent`.
        environment_kwargs: See `build_agent`.
        agent_config: See `build_agent`.
        model_kwargs: See `build_agent`.

    Returns:
        The agent's exit dict, with at least "exit_status" and "submission"
        keys (see `DefaultAgent.run`).
    """
    agent = build_agent(
        model_name,
        environment=environment,
        environment_kwargs=environment_kwargs,
        agent_config=agent_config,
        model_kwargs=model_kwargs,
    )
    return agent.run(task)
