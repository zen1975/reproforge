from pathlib import Path

from reproforge.registry import load_capability, validate_registry
from reproforge.validation import load_document, validate_document

ROOT = Path(__file__).resolve().parents[1]


def test_example_capability_validates():
    capability = load_capability(
        ROOT / "templates" / "capability.example.yaml",
        ROOT / "schemas" / "capability.schema.json",
    )
    assert capability["id"] == "example.echo"
    assert capability["runtime"]["deterministic"] is True


def test_registry_structure_is_valid():
    registry = load_document(ROOT / "registry" / "capabilities.json")
    assert validate_registry(registry, registry["capabilities"]) == []


def test_duplicate_capability_ids_are_rejected():
    registry = {"schema_version": "1.0.0", "capabilities": []}
    capability = {"id": "duplicate"}
    assert validate_registry(registry, [capability, capability]) == [
        "capability ids must be unique"
    ]


def test_first_ingested_study_manifest_validates():
    manifest = load_document(ROOT / "studies" / "arxiv-2610.03213" / "manifest.yaml")
    schema = load_document(ROOT / "schemas" / "paper-manifest.schema.json")
    assert validate_document(manifest, schema) == []
    assert manifest["paper"]["arxiv_id"] == "2610.03213"
    assert manifest["paper"]["license_status"] == "VERIFIED"
    assert manifest["paper"]["license"] == "CC BY-NC-ND 4.0"
    assert manifest["claims"][0]["id"] == "C1-task-tool-relevance"


def test_first_paper_derived_capability_validates_and_remains_experimental():
    capability = load_capability(
        ROOT / "capabilities" / "agent.task-tool-relevance-classifier" / "capability.yaml",
        ROOT / "schemas" / "capability.schema.json",
    )
    assert capability["status"] == "experimental"
    assert capability["evidence"]["reproduction_status"] == "PARTIAL"

    registry = load_document(ROOT / "registry" / "capabilities.json")
    descriptor = next(
        item
        for item in registry["capabilities"]
        if item["id"] == "agent.task-tool-relevance-classifier"
    )
    schema = load_document(ROOT / "schemas" / "capability.schema.json")
    assert validate_document(descriptor, schema) == []
    assert descriptor["evidence"]["studies"] == ["studies/arxiv-2610.03213"]
    assert descriptor["evidence"]["reproduction_status"] == "PARTIAL"
