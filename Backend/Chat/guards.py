"""Input guards: validate the question and spot small talk before any retrieval."""

import re

from django.conf import settings

RAG = "rag"
SMALLTALK = "smalltalk"

_PATTERNS = {
    "greeting": re.compile(
        r"h+i+|he+y+|he+l+o+|hola|namaste|good (morning|afternoon|evening)|(hi|hello|hey) there"
    ),
    "thanks": re.compile(r"thanks|thank you|thx|ty|thanks a lot|thank you (so|very) much"),
    "bye": re.compile(r"bye|goodbye|see you|see you later|good night"),
    "help": re.compile(r"help|what can you do|who are you|what do you do"),
}

REPLIES = {
    "greeting": "Hello! Upload a document, then ask me anything about it.",
    "thanks": "You're welcome! Ask me anything else about your documents.",
    "bye": "Goodbye! Come back anytime you have questions about your documents.",
    "help": (
        "I answer questions using only the documents you've uploaded, and I cite the "
        "passages I used. Upload a file, then ask away."
    ),
}


def validate_question(question: str, max_chars: int | None = None) -> tuple[bool, str]:
    """Return (is_valid, message). The message explains why a question was rejected."""
    if max_chars is None:
        max_chars = getattr(settings, "RAG_MAX_QUESTION_CHARS", 2000)
    text = (question or "").strip()
    if not text:
        return False, "Please enter a question."
    if len(text) > max_chars:
        return False, f"Your question is too long. Please keep it under {max_chars} characters."
    return True, ""


def _kind(question: str) -> str | None:
    text = re.sub(r"[^a-z\s']", " ", (question or "").lower())
    text = re.sub(r"\s+", " ", text).strip()
    for kind, pattern in _PATTERNS.items():
        if pattern.fullmatch(text):
            return kind
    return None


def classify_question(question: str) -> str:
    """'smalltalk' for greetings/thanks/bye/help-only messages, otherwise 'rag'."""
    return SMALLTALK if _kind(question) else RAG


def smalltalk_reply(question: str) -> str:
    return REPLIES[_kind(question) or "greeting"]