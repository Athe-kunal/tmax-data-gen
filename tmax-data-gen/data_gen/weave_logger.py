"""Shared W&B Weave tracing setup, reused across data_gen.

Import `weave_op` wherever a function's calls/inputs/outputs should be
traced to Weave (e.g. agent runs, LLM calls, verifiers). Weave is
initialized lazily on first use, so importing this module has no side
effects and is always safe.

Usage:
    from data_gen.weave_logger import weave_op

    @weave_op
    def solve(task: str) -> dict:
        ...
"""

from __future__ import annotations

import functools
import os
import threading
from typing import Any, Callable, TypeVar

import weave

_DEFAULT_PROJECT = "tmax-data-gen"

_init_lock = threading.Lock()
_initialized = False

_F = TypeVar("_F", bound=Callable[..., Any])


def init_weave(project_name: str | None = None) -> None:
    """Initializes the Weave client for this process, once.

    Safe to call multiple times or from multiple threads; only the first
    call actually initializes Weave.

    Args:
        project_name: W&B project to log traces to. Defaults to the
            WEAVE_PROJECT env var, falling back to "tmax-data-gen".
    """
    global _initialized
    if _initialized:
        return
    with _init_lock:
        if _initialized:
            return
        project = project_name or os.environ.get("WEAVE_PROJECT", _DEFAULT_PROJECT)
        weave.init(project)
        _initialized = True


def weave_op(func: _F) -> _F:
    """Decorator that traces a function's calls to Weave.

    Wraps `weave.op` and ensures `init_weave()` has run first, so any
    function in the codebase can be decorated without each call site
    worrying about initialization order.
    """
    traced = weave.op(func)

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        init_weave()
        return traced(*args, **kwargs)

    return wrapper  # type: ignore[return-value]
