import os
from typing import Any

import requests


DMR_BASE_URL = os.getenv("DMR_BASE_URL", "http://model-runner.docker.internal:12434/v1")
DMR_MODEL = os.getenv("DMR_MODEL", "hf.co/Qwen/Qwen3.5-4B")
REQUEST_TIMEOUT = int(os.getenv("DMR_TIMEOUT_SECONDS", "120"))


class ModelClientError(RuntimeError):
    pass


def get_models() -> dict[str, Any]:
    url = f"{DMR_BASE_URL}/models"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def generate_chat_completion(
    system_prompt: str,
    user_prompt: str,
    temperature: float,
    max_tokens: int,
    enable_thinking: bool,
) -> dict[str, Any]:
    url = f"{DMR_BASE_URL}/chat/completions"

    payload = {
        "model": DMR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
        "enable_thinking": enable_thinking,
    }

    try:
        resp = requests.post(url, json=payload, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        raise ModelClientError(f"Failed to call Docker Model Runner: {e}") from e

    data = resp.json()

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise ModelClientError(f"Unexpected model response: {data}") from e

    return {
        "raw": data,
        "content": content,
    }