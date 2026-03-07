import os
from typing import Any

import requests

DMR_BASE_URL = os.getenv("DMR_BASE_URL", "http://model-runner.docker.internal:12434/engines/v1")
DMR_MODEL = os.getenv("DMR_MODEL", "docker.io/ai/qwen2.5:latest")
REQUEST_TIMEOUT = int(os.getenv("DMR_TIMEOUT_SECONDS", "120"))


class ModelClientError(RuntimeError):
    pass


def get_models() -> dict[str, Any]:
    url = f"{DMR_BASE_URL}/models"
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as e:
        raise ModelClientError(f"Failed to fetch models from DMR: {e}") from e


def generate_chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
    max_tokens: int = 700,
    enable_thinking: bool = False,
) -> dict[str, Any]:
    url = f"{DMR_BASE_URL}/chat/completions"

    messages = []
    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_prompt})

    payload = {
        "model": DMR_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    _ = enable_thinking

    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        raw = resp.json()
    except requests.RequestException as e:
        raise ModelClientError(f"DMR chat completion request failed: {e}") from e

    try:
        content = raw["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ModelClientError(f"Unexpected DMR response format: {raw}") from e

    return {
        "content": content,
        "raw": raw,
    }