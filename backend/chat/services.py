import requests
from django.conf import settings


def ollama_options(model: str) -> dict:
    """
    Speed-related fields for an Ollama request: keep_alive (model stays loaded) and,
    for thinking-capable models such as Qwen3, the `think` flag from settings.
    """
    options = {}
    if settings.OLLAMA_KEEP_ALIVE:
        options["keep_alive"] = settings.OLLAMA_KEEP_ALIVE
    base_name = model.split(":")[0].lower()
    if settings.OLLAMA_THINK is not None and base_name in settings.OLLAMA_THINKING_MODELS:
        options["think"] = settings.OLLAMA_THINK
    return options


def ask_ollama(message: str) -> str:
    """
    Sends a prompt to the locally running Ollama server's /api/generate endpoint.
    Strictly uses local on-premise Ollama instance without external AI fallback.
    """
    response = requests.post(
        f"{settings.OLLAMA_URL}/api/generate",
        json={
            "model": settings.OLLAMA_MODEL,
            "prompt": message,
            "stream": False,
            **ollama_options(settings.OLLAMA_MODEL),
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")
