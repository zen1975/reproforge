"""ReproForge command-line interface."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .environment import capture_environment
from .hashing import sha256_object
from .validation import load_document, validate_document


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _schema_path(name: str) -> Path:
    return _root() / "schemas" / name


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


def cmd_validate_candidates(path: str) -> int:
    document = load_document(path)
    schema = load_document(_schema_path("candidate-queue.schema.json"))
    errors = validate_document(document, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    candidates = document.get("candidates", [])
    ids = [item["arxiv_id"] for item in candidates]
    if len(ids) != len(set(ids)):
        print("ERROR: duplicate arXiv IDs in candidate queue")
        return 1

    promoted = [
        item for item in candidates
        if item["status"] == "PROMOTED_TO_STUDY"
    ]
    for item in promoted:
        study_path = _root() / "studies" / f"arxiv-{item['arxiv_id']}"
        if not study_path.exists():
            print(f"ERROR: promoted candidate has no study directory: {study_path}")
            return 1

    print(f"VALID {path}")
    print(f"candidate_queue_sha256={sha256_object(document)}")
    print(f"candidate_count={len(candidates)}")
    return 0


def _resolve_status_path(path: str) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        candidate = candidate / "status.yaml"
    return candidate


def cmd_validate_status(path: str) -> int:
    status_path = _resolve_status_path(path)
    document = load_document(status_path)
    schema = load_document(_schema_path("study-status.schema.json"))
    errors = validate_document(document, schema)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    handoff = document["handoff"]
    if handoff["ready"]:
        handoff_path = _root() / handoff["path"]
        if not handoff_path.exists():
            print(f"ERROR: ready handoff does not exist: {handoff_path}")
            return 1

    if document["lifecycle"] == "HEAVY_COMPUTE_READY":
        if not document["free_light_phase_complete"]:
            print("ERROR: HEAVY_COMPUTE_READY requires free_light_phase_complete=true")
            return 1
        if not handoff["ready"]:
            print("ERROR: HEAVY_COMPUTE_READY requires handoff.ready=true")
            return 1

    print(f"VALID {status_path}")
    print(f"status_sha256={sha256_object(document)}")
    return 0


def cmd_study_status(path: str) -> int:
    status_path = _resolve_status_path(path)
    if cmd_validate_status(str(status_path)) != 0:
        return 1
    document = load_document(status_path)
    print()
    print(f"study_id={document['study_id']}")
    print(f"lifecycle={document['lifecycle']}")
    print(f"reproduction_status={document['reproduction_status']}")
    print(f"free_light_phase_complete={str(document['free_light_phase_complete']).lower()}")
    print(f"boundary={document['current_boundary']}")
    print(f"next_step={document['next_step']}")
    print(f"handoff={document['handoff']['path']}")
    blockers = document.get("blockers", [])
    if blockers:
        print("blockers:")
        for blocker in blockers:
            print(f"  - {blocker}")
    return 0


def cmd_validate_all_statuses() -> int:
    study_root = _root() / "studies"
    paths = sorted(study_root.glob("*/status.yaml"))
    if not paths:
        print("ERROR: no study status files found")
        return 1
    failed = False
    for path in paths:
        print(f"==> {path.parent.name}")
        if cmd_validate_status(str(path)) != 0:
            failed = True
    return 1 if failed else 0


def main() -> None:
    parser = argparse.ArgumentParser(prog="reproforge")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate a paper manifest")
    validate.add_argument("path")

    validate_candidates = sub.add_parser(
        "validate-candidates", help="validate a research candidate queue"
    )
    validate_candidates.add_argument("path")

    validate_status = sub.add_parser("validate-status", help="validate one study status")
    validate_status.add_argument("path")

    study_status = sub.add_parser("study-status", help="show one study lifecycle and handoff")
    study_status.add_argument("path")

    sub.add_parser("validate-all-statuses", help="validate all study lifecycle files")
    sub.add_parser("environment", help="print environment evidence as JSON")

    args = parser.parse_args()
    if args.command == "validate":
        raise SystemExit(cmd_validate(args.path))
    if args.command == "validate-candidates":
        raise SystemExit(cmd_validate_candidates(args.path))
    if args.command == "validate-status":
        raise SystemExit(cmd_validate_status(args.path))
    if args.command == "study-status":
        raise SystemExit(cmd_study_status(args.path))
    if args.command == "validate-all-statuses":
        raise SystemExit(cmd_validate_all_statuses())
    if args.command == "environment":
        print(json.dumps(capture_environment(), indent=2, sort_keys=True))
        raise SystemExit(0)


if __name__ == "__main__":
    main()
