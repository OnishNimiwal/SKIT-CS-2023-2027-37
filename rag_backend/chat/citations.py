"""Citation handling: keep only the passages the answer actually cites."""

import re

CITATION_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")


def cited_indexes(answer: str, max_index: int) -> list[int]:
    """Numbers cited in the answer as [1], [2][3] or [1, 2], ignoring out-of-range ones."""
    found: set[int] = set()
    for match in CITATION_RE.finditer(answer or ""):
        for part in match.group(1).split(","):
            n = int(part.strip())
            if 1 <= n <= max_index:
                found.add(n)
    return sorted(found)


def select_citations(answer: str, citations: list[dict]) -> list[dict]:
    """Return only the cited citations; if the answer cites nothing, return them all."""
    cited = set(cited_indexes(answer, len(citations)))
    if not cited:
        return list(citations)
    return [c for c in citations if c["index"] in cited]