import requests
from django.conf import settings

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
        },
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("response", "")
