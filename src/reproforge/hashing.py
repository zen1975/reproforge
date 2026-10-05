"""Stable hashing helpers for manifests and evidence."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json(value: Any) -> str:
    """Return deterministic JSON suitable for hashing."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_object(value: Any) -> str:
    """Hash a JSON-compatible object deterministically."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()
