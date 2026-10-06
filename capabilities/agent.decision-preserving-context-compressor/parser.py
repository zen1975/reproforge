"""Strict parser for FOCUS-style draft plan dependency citations."""

from __future__ import annotations

import re

_DEPENDS = re.compile(r"Depends on:\s*\[([^\]]*)\]", re.IGNORECASE)
_RESCUED = re.compile(r"Rescued Spans:\s*\[([^\]]*)\]", re.IGNORECASE)
_SPAN = re.compile(r"^s_[A-Za-z0-9_-]+$")


def _ids(body: str) -> set[str]:
    out = set()
    for raw in body.split(","):
        value = raw.strip()
        if not value:
            continue
        if not _SPAN.match(value):
            raise ValueError(f"invalid span id: {value}")
        out.add(value)
    return out


def parse_plan(text: str) -> tuple[set[str], set[str]]:
    dependency_matches = list(_DEPENDS.finditer(text))
    if not dependency_matches:
        raise ValueError("no dependency citation lines found")
    dependencies: set[str] = set()
    for match in dependency_matches:
        dependencies |= _ids(match.group(1))

    rescued: set[str] = set()
    matches = list(_RESCUED.finditer(text))
    if matches:
        rescued = _ids(matches[-1].group(1))
    return dependencies, rescued
