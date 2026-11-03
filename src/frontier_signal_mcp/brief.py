"""Strip gated watchlist content from brief markdown before serving."""

from __future__ import annotations

import re

GATED_HEADING = re.compile(r"(?im)^#{1,6}\s+.*\bgated\b.*$")
WATCHLIST_ONLY = re.compile(
    r"(?im)^#{1,6}\s+.*\bwatchlist\b.*\b(login|members?|gated)\b.*$",
)
TRAILING_RULE = re.compile(r"(?:\r?\n)-{3,}\s*$")


def public_brief_only(markdown: str) -> str:
    """Return the public portion of a brief, dropping gated watchlist copy.

    Cuts at the first markdown heading whose title contains "gated", or a
    heading that marks watchlist-login-only content. Does not invent a brief
    if the file is empty after the cut.
    """
    text = markdown.replace("\r\n", "\n")
    cut_at: int | None = None
    for pattern in (GATED_HEADING, WATCHLIST_ONLY):
        match = pattern.search(text)
        if match is not None:
            cut_at = match.start() if cut_at is None else min(cut_at, match.start())
    if cut_at is not None:
        text = text[:cut_at]
    text = TRAILING_RULE.sub("", text.rstrip())
    if text:
        text += "\n"
    return text
