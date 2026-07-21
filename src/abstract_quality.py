"""Shared quality gate for fetched abstracts.

Some sources (notably CrossRef for ACL Anthology records) return an author
list and proceedings title in the abstract field instead of a real abstract.
Storing those pollutes search and topic analysis, so every fetched abstract
passes through :func:`looks_like_abstract` before it reaches the database.
"""

from __future__ import annotations

import re

MIN_ABSTRACT_LENGTH = 100

# "Jane Doe, John Roe, ... . Proceedings of the ..." — the ACL Anthology
# metadata string that CrossRef sometimes returns in place of an abstract.
# A name token is a capitalized word or single initial (e.g. "S", "Sakshi").
_NAME = r"[A-Z][\w.'-]*"
_AUTHOR_LIST_PROCEEDINGS = re.compile(
    rf"^(?:{_NAME} )+{_NAME}"                       # a full name
    rf"(?:,\s*(?:and\s+)?(?:{_NAME} )+{_NAME})*"    # more names, comma-separated
    r"\.?\s*Proceedings of",
    re.IGNORECASE,
)


def looks_like_abstract(text: str | None) -> bool:
    """Return True when ``text`` reads like a real abstract, not metadata.

    Rejects empty/short text, author-list-plus-proceedings strings, and text
    with no lowercase prose (e.g. an all-caps title echoed back).
    """
    if not text:
        return False
    stripped = text.strip()
    if len(stripped) < MIN_ABSTRACT_LENGTH:
        return False
    if _AUTHOR_LIST_PROCEEDINGS.match(stripped):
        return False
    letters = [character for character in stripped if character.isalpha()]
    if not letters:
        return False
    lowercase_ratio = sum(character.islower() for character in letters) / len(letters)
    return lowercase_ratio >= 0.5
