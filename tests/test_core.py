from pathlib import Path

from reproforge.hashing import sha256_object
from reproforge.validation import load_document, validate_document
from reproforge.verdict import Verdict, aggregate_verdict


ROOT = Path(__file__).resolve().parents[1]


def test_hash_is_order_independent_for_objects():
    assert sha256_object({"a": 1, "b": 2}) == sha256_object({"b": 2, "a": 1})


def test_verdict_aggregation_is_conservative():
    assert aggregate_verdict([Verdict.PASS, Verdict.PASS]) == Verdict.PASS
    assert aggregate_verdict([Verdict.PASS, Verdict.PARTIAL]) == Verdict.PARTIAL
    assert aggregate_verdict([Verdict.PASS, Verdict.INCONCLUSIVE]) == Verdict.INCONCLUSIVE
    assert aggregate_verdict([Verdict.PASS, Verdict.FAIL]) == Verdict.FAIL
    assert aggregate_verdict([]) == Verdict.INCONCLUSIVE


def test_example_manifest_validates():
    manifest = load_document(ROOT / "templates" / "paper-manifest.example.yaml")
    schema = load_document(ROOT / "schemas" / "paper-manifest.schema.json")
    assert validate_document(manifest, schema) == []
