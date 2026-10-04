from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class ModelError(RuntimeError):
    """A live model request could not be completed."""


@dataclass
class ModelResponse:
    message: dict[str, Any]
    usage: dict[str, int]


class OpenAIChatClient:
    """Small dependency-free client for the OpenAI-compatible chat endpoint."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: int = 90):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ModelError("OPENAI_API_KEY is required for a live evaluation")
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.timeout = timeout

    def complete(
        self,
        *,
        model: str,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        json_mode: bool = False,
    ) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "store": False,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1000]
            raise ModelError(f"Model API returned HTTP {exc.code}: {detail}") from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ModelError(f"Model API request failed: {exc}") from exc
        try:
            message = body["choices"][0]["message"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ModelError("Model API returned an unexpected response shape") from exc
        usage = body.get("usage") or {}
        return ModelResponse(message=message, usage={k: int(v) for k, v in usage.items() if isinstance(v, int)})
