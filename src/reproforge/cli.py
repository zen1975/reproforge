"""ReproForge command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .environment import capture_environment
from .hashing import sha256_object
from .validation import load_document, validate_document


def _schema_path(name: str) -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "schemas" / name


def cmd_validate(path: str) -> int:
    document = load_document(path)
    schema = load_document(_schema_path("paper-manifest.schema.json"))
    errors = validate_document(document, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"VALID {path}")
    print(f"manifest_sha256={sha256_object(document)}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="reproforge")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a paper manifest")
    validate.add_argument("path")

    sub.add_parser("environment", help="print environment evidence as JSON")

    args = parser.parse_args()
    if args.command == "validate":
        raise SystemExit(cmd_validate(args.path))
    if args.command == "environment":
        print(json.dumps(capture_environment(), indent=2, sort_keys=True))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
