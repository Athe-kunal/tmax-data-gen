"""Shared helpers for driving a mini-swe-agent environment's own `execute()`
interface directly - installing packages, writing/reading files via a
base64 shell pipe rather than a backend-specific SDK call (cwsandbox's
write_file, daytona's sandbox.fs.upload_file, ...) - so the same code works
identically for any environment (sandbox, daytona, docker, local).

Used by data_gen.rollout, data_gen.multi_turn_rollout, and data_gen.tmax_rl_seed.
"""

from __future__ import annotations

import base64


def run(env, command: str) -> dict:
    """Runs `command` through an environment's own execute(); raises on nonzero exit."""
    result = env.execute({"command": command})
    if result["returncode"] != 0:
        raise RuntimeError(f"Command failed ({result['returncode']}): {command}\n{result['output']}")
    return result


def write_file(env, path: str, content: bytes) -> None:
    """Writes `content` to `path` inside the environment via a base64 shell pipe."""
    encoded = base64.b64encode(content).decode()
    run(env, f"mkdir -p {path.rsplit('/', 1)[0]} && echo {encoded} | base64 -d > {path}")


def read_file(env, path: str) -> str:
    return run(env, f"cat {path}")["output"]
