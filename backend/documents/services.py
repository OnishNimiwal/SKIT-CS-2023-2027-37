import requests
from django.conf import settings

class OllamaServiceError(Exception):
    """Raised when communication with Ollama server fails."""
    pass

def _query_ollama(prompt: str) -> str:
    """Sends prompt to local Ollama instance and returns generated text."""
    try:
        response = requests.post(
            f"{settings.OLLAMA_URL}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
            timeout=120,
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "").strip()
    except requests.exceptions.RequestException as exc:
        raise OllamaServiceError(f"Local AI server is unavailable: {str(exc)}") from exc
    except Exception as exc:
        raise OllamaServiceError(f"Unexpected error communicating with Ollama: {str(exc)}") from exc

def ask_document_question(document_text: str, question: str, filename: str = "") -> str:
    """
    Asks a question about a specific document context using the local Ollama model.
    """
    prompt = (
        f"You are an on-premise local AI assistant analyzing the document '{filename}'.\n"
        "Answer the user's question thoroughly and accurately based on the provided document content.\n"
        "If the answer cannot be determined from the document, clearly mention that.\n\n"
        "=== DOCUMENT CONTENT ===\n"
        f"{document_text}\n"
        "=== END DOCUMENT CONTENT ===\n\n"
        f"USER QUESTION: {question}\n\n"
        "ANSWER:"
    )
    return _query_ollama(prompt)

def summarize_document(document_text: str, filename: str = "") -> str:
    """
    Generates an executive summary of the document using the local Ollama model.
    """
    prompt = (
        f"You are an on-premise local AI assistant analyzing the document '{filename}'.\n"
        "Generate a structured, professional summary of this document.\n"
        "Include:\n"
        "1. Executive Overview\n"
        "2. Key Points & Findings\n"
        "3. Important Details & Conclusions\n\n"
        "=== DOCUMENT CONTENT ===\n"
        f"{document_text}\n"
        "=== END DOCUMENT CONTENT ===\n\n"
        "EXECUTIVE SUMMARY:"
    )
    return _query_ollama(prompt)
