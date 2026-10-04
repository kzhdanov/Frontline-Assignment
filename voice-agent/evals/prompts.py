from __future__ import annotations

import importlib
import importlib.util
import sys
import types
from pathlib import Path
from typing import Callable


def _load_voice_prompt() -> types.ModuleType:
    """Load production prompt code without importing integration-heavy src.__init__."""
    try:
        return importlib.import_module("voice_prompt")
    except ModuleNotFoundError:
        # The installed application path works normally. A source-only eval
        # environment may lack httpx/supabase imported by shared/src/__init__.
        # Load only the dependency-free production negotiation_prompt module.
        shared_src = Path(__file__).resolve().parents[2] / "shared" / "src"
        package = types.ModuleType("src")
        package.__path__ = [str(shared_src)]  # type: ignore[attr-defined]
        sys.modules["src"] = package
        spec = importlib.util.spec_from_file_location(
            "src.negotiation_prompt", shared_src / "negotiation_prompt.py"
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("Unable to load production negotiation prompt")
        module = importlib.util.module_from_spec(spec)
        sys.modules["src.negotiation_prompt"] = module
        spec.loader.exec_module(module)
        sys.modules.pop("voice_prompt", None)
        return importlib.import_module("voice_prompt")


_VOICE_PROMPT = _load_voice_prompt()


def initial_prompt(organization: str) -> str:
    function: Callable[..., str] = _VOICE_PROMPT.get_initial_greeting_prompt
    return function(organization, phone_first_enabled=False)


def negotiation_prompt(load: dict) -> str:
    function: Callable[[dict], str] = _VOICE_PROMPT.build_full_negotiation_prompt
    return function(load)

