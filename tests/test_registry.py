from pathlib import Path

from reproforge.registry import load_capability, validate_registry
from reproforge.validation import load_document

ROOT = Path(__file__).resolve().parents[1]


def test_example_capability_validates():
    capability = load_capability(
        ROOT / "templates" / "capability.example.yaml",
        ROOT / "schemas" / "capability.schema.json",
    )
    assert capability["id"] == "example.echo"
    assert capability["runtime"]["deterministic"] is True


def test_empty_registry_is_valid():
    registry = load_document(ROOT / "registry" / "capabilities.json")
    assert validate_registry(registry, []) == []


def test_duplicate_capability_ids_are_rejected():
    registry = {"schema_version": "1.0.0", "capabilities": []}
    capability = {"id": "duplicate"}
    assert validate_registry(registry, [capability, capability]) == [
        "capability ids must be unique"
    ]
