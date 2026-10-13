"""Per-arm runner for jev-live-systemone-check-v3a (LOCAL ONLY; keys only in the process environment).

    TYPESAFE_API_KEY=...  SSL_CERT_FILE=/etc/ssl/cert.pem python jev_v3_run.py --arm jev     --phase pilot --out X.json
    ANTHROPIC_API_KEY=... python jev_v3_run.py --arm control --phase pilot --out Y.json
    ANTHROPIC_API_KEY=... python jev_v3_run.py --arm b       --phase pilot --out Z.json

v3a = B (free-generation baseline analogue), C (LLM candidate-interface control) and J (Jev) on the FROZEN v2
generator g2 with fresh, disjoint seeds. v2 code is imported read-only; the v2 freeze pin must still verify.
One process = one arm = one key = one sanitized evidence file. Phase `test` is refused unless the v3a pin in
jev_v3a_freeze.json matches the v3a files AND the v2 pin still matches. Without a key: SKIPPED_NO_CREDENTIAL.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jev_v2_arms as v2arms  # noqa: E402
import jev_v2_core as core  # noqa: E402
import jev_v2_generator as gen  # noqa: E402
import jev_v2_run as v2run  # noqa: E402
import jev_v3_arms as v3arms  # noqa: E402

v1 = core.v1
EXPERIMENT_ID = "jev-live-systemone-check-v3a"
FREEZE_FILES = ("jev_v3_arms.py", "jev_v3_run.py", "jev_v3_analysis.py")
_PIN = HERE / "jev_v3a_freeze.json"
_PIN_DATA = json.loads(_PIN.read_text()) if _PIN.exists() else {}
FREEZE_SHA256 = _PIN_DATA.get("freeze_sha256")
PILOT_SEEDS = range(5000, 5004)   # 4 per family
TEST_SEEDS = range(4000, 4012)    # 12 per family (never run before the v3a freeze)
USED_SEEDS = (set(gen.PILOT_SEEDS) | set(gen.TEST_SEEDS) | set(range(1000, 1004)))  # v2 pilots + v2 test + g1 pilot
ARMS = ("jev", "control", "b")
KEY_ENV = {"jev": "TYPESAFE_API_KEY", "control": "ANTHROPIC_API_KEY", "b": "ANTHROPIC_API_KEY"}
PRICING = {"jev": v2run.PRICING["jev"], "control": v2arms.CONTROL_PRICING, "b": v3arms.B_PRICING}
ARM_CAP_USD = {"jev": 0.5, "control": 1.5, "b": 3.0}  # sums to the proposed US$5 v3a cap
RESOLVED = {"jev": "jev-1.13.0", "control": v2arms.CONTROL_MODEL, "b": v3arms.B_MODEL}
ARM_LABEL = {
    "jev": "Jev (jev-1.13.0)",
    "control": f"LLM candidate-interface control ({v2arms.CONTROL_MODEL})",
    "b": f"LLM free-generation baseline analogue ({v3arms.B_MODEL}; not the paper's B)",
}
CLAIM_SCOPE = (
    "Three-arm contrast on the frozen v2 stress fixture (generator g2, fresh seeds): B = free-generation "
    "baseline analogue, C = LLM candidate-interface control, J = Jev. B is an analogue, not the paper's B. "
    "Not an ALFWorld/AndroidWorld reproduction and not an estimate of the paper's effect sizes; descriptive only."
)
ORDERS = v2run.ORDERS


def freeze_sha256() -> str:
    h = hashlib.sha256()
    for name in FREEZE_FILES:
        h.update(name.encode() + b"\0" + (HERE / name).read_bytes() + b"\0")
    return h.hexdigest()


def v2_pin_intact() -> bool:
    return v2run.FREEZE_SHA256 is not None and v2run.FREEZE_SHA256 == v2run.freeze_sha256()


def seeds_for(phase: str) -> range:
    return PILOT_SEEDS if phase == "pilot" else TEST_SEEDS


def instances_for(phase: str) -> list[dict]:
    seeds = seeds_for(phase)
    assert not (set(seeds) & USED_SEEDS), "v3a seeds must be disjoint from every earlier run"
    assert not (set(PILOT_SEEDS) & set(TEST_SEEDS)), "pilot and test seeds must be disjoint"
    return gen.generate(seeds)


def expected_rows(phase: str) -> int:
    return len(instances_for(phase)) * len(ORDERS) * 2


def build_evidence(arm: str, phase: str, rows: list[dict], status: str, identity: dict, spent: float,
                   cap: float) -> dict:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": phase, "arm": arm, "status": status,
        "generator_version": gen.GENERATOR_VERSION, "arm_label": ARM_LABEL[arm],
        "freeze_sha256": freeze_sha256(), "v2_freeze_sha256": v2run.freeze_sha256(),
        "execution_environment": "local", "spend_usd": spent, "spend_cap_usd": cap,
        "expected_rows": expected_rows(phase), "identity": identity,
        "aggregate": v2run.aggregate(rows) if rows else None, "rows": rows, "claim_scope": CLAIM_SCOPE,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--phase", choices=("pilot", "test"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cap-usd", type=float)
    args = ap.parse_args(argv)
    cap = min(args.cap_usd if args.cap_usd is not None else ARM_CAP_USD[args.arm], ARM_CAP_USD[args.arm])
    key = os.environ.get(KEY_ENV[args.arm], "").strip()
    if not key:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "arm": args.arm, "status": "SKIPPED_NO_CREDENTIAL",
                          "detail": f"{KEY_ENV[args.arm]} is not set; no API call, no evidence."}, indent=2))
        return 0
    if args.phase == "test" and (FREEZE_SHA256 is None or FREEZE_SHA256 != freeze_sha256() or not v2_pin_intact()):
        print("REFUSED: test phase requires the pinned v3a freeze hash and an intact v2 pin.", file=sys.stderr)
        return 4
    pricing = PRICING[args.arm]
    guard = v2arms.SpendGuard(cap, pricing)
    if args.arm == "jev":
        client = v1.JevClient(v1.load_fixture()["api"], key)
        identity = v2run.jev_identity(client)
        selector = v2arms.JevArm(client, guard=guard)
    else:
        try:
            import anthropic
        except ImportError:
            print("pip install 'anthropic>=1,<2' (optional extra: reproforge[control])", file=sys.stderr)
            return 5
        client = anthropic.Anthropic(api_key=key, max_retries=0, timeout=60.0)
        identity = v2run.control_identity(client)
        selector = (v2arms.ControlArm if args.arm == "control" else v3arms.BArm)(client, guard=guard)
    if identity.get("resolved_model") != RESOLVED[args.arm]:
        print(json.dumps({"status": "ABORTED_IDENTITY_FAILED", "identity_keys": sorted(identity)}), file=sys.stderr)
        return 3
    partial = Path(args.out + ".partial.jsonl")
    with partial.open("w") as fh:
        rows, status = v2run.run_phase(
            selector, args.arm, instances_for(args.phase), pricing,
            progress=lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", file=sys.stderr, flush=True),
            checkpoint=lambda r: (fh.write(json.dumps(r) + "\n"), fh.flush()))
    evidence = build_evidence(args.arm, args.phase, rows, status, json.loads(json.dumps(identity)), guard.spent, cap)
    text = json.dumps(evidence, indent=2, sort_keys=True)
    if key in text:
        print("ABORT: credential value found in output; refusing to write.", file=sys.stderr)
        return 2
    Path(args.out).write_text(text + "\n")
    partial.unlink(missing_ok=True)
    print(json.dumps({"arm": args.arm, "phase": args.phase, "status": status, "rows": len(rows),
                      "spend_usd": guard.spent}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
