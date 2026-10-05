"""Capability registry loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reproforge.validation import load_document, validate_document


def load_capability(path: str | Path, schema_path: str | Path) -> dict[str, Any]:
    """Load and validate one capability descriptor."""
    capability = load_document(path)
    schema = load_document(schema_path)
    errors = validate_document(capability, schema)
    if errors:
        raise ValueError("invalid capability: " + "; ".join(errors))
    return capability


def validate_registry(registry: dict[str, Any], capabilities: list[dict[str, Any]]) -> list[str]:
    """Validate registry-level invariants after capability schema validation."""
    errors: list[str] = []
    if registry.get("schema_version") != "1.0.0":
        errors.append("unsupported registry schema_version")

    declared = registry.get("capabilities")
    if not isinstance(declared, list):
        errors.append("registry capabilities must be a list")
        return errors

    ids = [capability.get("id") for capability in capabilities]
    if len(ids) != len(set(ids)):
        errors.append("capability ids must be unique")
    return errors
