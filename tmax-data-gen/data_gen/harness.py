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
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel

from data_gen.browser_setup import DEFAULT_MULTIMODAL_REGEX
from data_gen.daytona_environment import DaytonaEnvironment
from data_gen.sandbox_environment import SandboxEnvironment
from data_gen.weave_logger import weave_op

# Two mutually-consistent (model class, config) pairings - mismatching them
# silently breaks every turn (each config's prompt describes the *other*
# class's action format, so nothing the model says ever parses):
#   "text":     LitellmTextbasedModel + default.yaml (regex-parses one
#               ```mswea_bash_command block from plain text)
#   "toolcall": LitellmModel + mini.yaml (always passes tools=[BASH_TOOL],
#               only ever parses native tool_calls)
# Neither is universally better - verified empirically, not assumed:
# Llama-3.3-70B-Instruct on Weave Inference is reliable in "text" mode but
# reverts to plain markdown (ignoring the tools it was offered) in
# "toolcall" mode on complex prompts; GLM-5.3-Flash showed the opposite
# problem in "text" mode (repeatedly failed to close its markdown fence
# correctly, hitting RepeatedFormatError before finishing real tasks it was
# otherwise solving correctly) and is expected to do better in "toolcall"
# mode since GLM is trained specifically for function-calling. Pick per
# model, not a fixed default.
_MODEL_STYLES: dict[str, tuple[type, Path]] = {
    "text": (LitellmTextbasedModel, package_dir / "config" / "default.yaml"),
    "toolcall": (LitellmModel, package_dir / "config" / "mini.yaml"),
}

_ENVIRONMENTS = {
    "local": LocalEnvironment,
    "docker": DockerEnvironment,
    "sandbox": SandboxEnvironment,
    "daytona": DaytonaEnvironment,
}


def load_default_agent_config(config_path: Path = _MODEL_STYLES["text"][1]) -> dict[str, Any]:
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
    model_style: Literal["text", "toolcall"] = "text",
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
            defaults bundled with mini-swe-agent for `model_style`.
        model_kwargs: Extra kwargs merged into every underlying
            `litellm.completion` call the model makes (e.g. `api_base`/
            `api_key`/`extra_headers` for a self-hosted or alternate
            OpenAI-compatible provider - see
            `data_gen.inference_config.OpenAICompatibleConfig.litellm_kwargs`).
        model_style: "text" (default) parses one ```mswea_bash_command
            markdown block from plain text - reliable for models that don't
            consistently emit native tool_calls, but may fumble the exact
            fence syntax. "toolcall" passes `tools=[BASH_TOOL]` and parses
            native tool_calls - better for models specifically trained for
            function-calling. See `_MODEL_STYLES`; pick per model based on
            actual observed behavior, not by default.

    Returns:
        A `DefaultAgent` instance, not yet run.
    """
    if environment not in _ENVIRONMENTS:
        raise ValueError(f"Unknown environment {environment!r}, expected one of {list(_ENVIRONMENTS)}")
    if model_style not in _MODEL_STYLES:
        raise ValueError(f"Unknown model_style {model_style!r}, expected one of {list(_MODEL_STYLES)}")

    env = _ENVIRONMENTS[environment](**(environment_kwargs or {}))
    model_class, config_path = _MODEL_STYLES[model_style]
    model_extra_kwargs: dict[str, Any] = {}
    if (environment_kwargs or {}).get("enable_browser"):
        # multimodal_regex is a top-level LitellmModel(Textbased)Config field
        # (not part of model_kwargs, which is forwarded to litellm.completion
        # calls) - it lets the model see /screenshot's
        # <MSWEA_MULTIMODAL_CONTENT>-tagged output (see
        # data_gen.browser_driver) as an actual image content block instead
        # of raw tagged text.
        model_extra_kwargs["multimodal_regex"] = DEFAULT_MULTIMODAL_REGEX
    # ignore_errors: litellm has no pricing entry for most self-hosted/custom
    # OpenAI-compatible models (e.g. Weave Inference's), so cost tracking
    # would otherwise raise on every single completion call.
    model = model_class(
        model_name=model_name,
        model_kwargs=model_kwargs or {},
        cost_tracking="ignore_errors",
        **model_extra_kwargs,
    )
    config = load_default_agent_config(config_path) | (agent_config or {})
    return DefaultAgent(model, env, **config)


@weave_op
def run_agent(
    task: str,
    model_name: str,
    environment: Literal["local", "docker", "sandbox", "daytona"] = "local",
    environment_kwargs: dict[str, Any] | None = None,
    agent_config: dict[str, Any] | None = None,
    model_kwargs: dict[str, Any] | None = None,
    model_style: Literal["text", "toolcall"] = "text",
) -> dict[str, Any]:
    """Builds an agent and runs it against a single task.

    Args:
        task: The task/problem statement to solve.
        model_name: LiteLLM model name.
        environment: "local", "docker", "sandbox", or "daytona". See `build_agent`.
        environment_kwargs: See `build_agent`.
        agent_config: See `build_agent`.
        model_kwargs: See `build_agent`.
        model_style: See `build_agent`.

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
        model_style=model_style,
    )
    return agent.run(task)
