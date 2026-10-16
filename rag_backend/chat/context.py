"""Context management: keep prompts inside the model's limited context window."""

from django.conf import settings

MIN_PARTIAL_CHARS = 200


def fit_chunks_to_budget(chunks: list[dict], max_chars: int | None = None) -> list[dict]:
    """
    Keep chunks in order while they fit in `max_chars`.
    If the next chunk doesn't fit, include a truncated copy only when enough room is left
    (or when it would be the only chunk), then stop.
    """
    if max_chars is None:
        max_chars = getattr(settings, "RAG_MAX_CONTEXT_CHARS", 6000)

    kept: list[dict] = []
    used = 0
    for c in chunks:
        size = len(c["text"])
        if used + size <= max_chars:
            kept.append(c)
            used += size
            continue
        remaining = max_chars - used
        if remaining > 0 and (not kept or remaining >= MIN_PARTIAL_CHARS):
            kept.append({**c, "text": c["text"][: max(remaining - 1, 0)].rstrip() + "…"})
        break
    return kept


def trim_history(messages, max_messages: int | None = None, max_chars: int | None = None) -> list:
    """
    Keep the most recent messages that fit the limits.
    The latest message is always kept, and the result starts on a user turn.
    """
    if max_messages is None:
        max_messages = getattr(settings, "RAG_HISTORY_MESSAGES", 10)
    if max_chars is None:
        max_chars = getattr(settings, "RAG_HISTORY_CHARS", 4000)

    msgs = list(messages)[-max(max_messages, 1):]
    while len(msgs) > 1 and sum(len(str(m.content)) for m in msgs) > max_chars:
        msgs.pop(0)
    while len(msgs) > 1 and msgs[0].type != "human":
        msgs.pop(0)
    return msgs