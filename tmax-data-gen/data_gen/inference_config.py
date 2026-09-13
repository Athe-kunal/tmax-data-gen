"""Configuration for routing litellm calls through an OpenAI-compatible endpoint.

Defaults to W&B Weave Inference (https://docs.wandb.ai/weave/guides/integrations/inference),
but every setting is a standard `OPENAI_*` env var so switching to a
different OpenAI-compatible provider (OpenAI itself, a self-hosted vLLM/MLX
server, Azure, etc.) later is just editing .env - no code change:

    OPENAI_API_KEY   - API key for the endpoint. Required.
    OPENAI_BASE_URL  - Endpoint base URL. Defaults to Weave Inference's
                        (config/inference.yaml's `base_url`).
    OPENAI_MODEL     - Model ID to use. Defaults to config/inference.yaml's
                        `default_model`.
    OPENAI_PROJECT   - Optional "<team>/<project>", sent as the
                        `OpenAI-Project` header (Weave Inference uses this
                        for usage attribution; harmless/ignored elsewhere).

Non-secret defaults (base URL, available model IDs) live in
config/inference.yaml. Secrets and per-environment overrides live in .env
(see .env.example) and are loaded via python-dotenv.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

_PACKAGE_DIR = Path(__file__).resolve().parent
_DEFAULT_CONFIG_PATH = _PACKAGE_DIR / "config" / "inference.yaml"
_DEFAULT_ENV_PATH = _PACKAGE_DIR.parent / ".env"

load_dotenv(_DEFAULT_ENV_PATH)


def load_inference_config(config_path: Path = _DEFAULT_CONFIG_PATH) -> dict:
    """Loads the `weave_inference:` section of config/inference.yaml."""
    return yaml.safe_load(config_path.read_text())["weave_inference"]


@dataclass(frozen=True)
class OpenAICompatibleConfig:
    """Resolved settings for one OpenAI-compatible-endpoint call."""

    base_url: str
    api_key: str | None
    project: str | None
    model: str

    @staticmethod
    def from_env(model: str | None = None, config_path: Path = _DEFAULT_CONFIG_PATH) -> "OpenAICompatibleConfig":
        """Builds a config from config/inference.yaml + .env / the environment.

        Args:
            model: Model ID to use (e.g. "meta-llama/Llama-3.1-8B-Instruct").
                Falls back to the OPENAI_MODEL env var, then
                config/inference.yaml's `default_model`.
            config_path: Path to the non-secret YAML config.
        """
        config = load_inference_config(config_path)
        return OpenAICompatibleConfig(
            base_url=os.environ.get("OPENAI_BASE_URL") or config["base_url"],
            api_key=os.environ.get("OPENAI_API_KEY"),
            project=os.environ.get("OPENAI_PROJECT"),
            model=model or os.environ.get("OPENAI_MODEL") or config["default_model"],
        )

    def litellm_model(self) -> str:
        """The `model=` string to pass to `litellm.completion`."""
        return f"openai/{self.model}"

    def litellm_kwargs(self) -> dict[str, object]:
        """Extra kwargs to merge into a `litellm.completion(...)` call."""
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and fill it in "
                "(for Weave Inference, get a key at https://wandb.ai/settings)."
            )
        kwargs: dict[str, object] = {"api_base": self.base_url, "api_key": self.api_key}
        if self.project:
            kwargs["extra_headers"] = {"OpenAI-Project": self.project}
        return kwargs
