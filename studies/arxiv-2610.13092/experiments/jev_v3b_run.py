"""Per-cell runner for jev-live-systemone-check-v3b (LOCAL ONLY; keys only in the process environment).

One process = one cell = (arm, overhead level) = one sanitized evidence file.
    TYPESAFE_API_KEY=... ANTHROPIC_API_KEY=... SSL_CERT_FILE=/etc/ssl/cert.pem \
        python jev_v3b_run.py --arm jev --overhead O1 --phase test --out ../evidence/jev_v3b_test_jev_O1.result.json
Arms use the frozen v3a adapters; O1 adds the auxiliary stage of jev_v3b_arms.py. Phase `test` is refused unless
the v3b pin matches and the v2 and v3a pins are intact. Phase `smoke` (3 instances, v3a pilot seeds) is for
checking the request path only; its output must not be written into the evidence directory.
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
import jev_v3_run as v3run  # noqa: E402
import jev_v3b_arms as auxarms  # noqa: E402

v1 = core.v1
EXPERIMENT_ID = "jev-live-systemone-check-v3b"
FREEZE_FILES = ("jev_v3b_arms.py", "jev_v3b_run.py", "jev_v3b_analysis.py")
_PIN = HERE / "jev_v3b_freeze.json"
FREEZE_SHA256 = json.loads(_PIN.read_text()).get("freeze_sha256") if _PIN.exists() else None
FAMILIES = ("anchor", "injected", "indirection")
TEST_SEEDS = range(6000, 6012)
SMOKE_SEEDS = range(5000, 5001)
USED_SEEDS = v3run.USED_SEEDS | set(v3run.PILOT_SEEDS) | set(v3run.TEST_SEEDS)
ARMS = v3run.ARMS
LEVELS = ("O0", "O1")
ORDERS = v2run.ORDERS
CELL_CAP_USD = {"jev": 0.2, "control": 0.5, "b": 0.7}   # selector spend per cell
AUX_CAP_USD = 0.4                                        # auxiliary spend per O1 cell (total worst case US$4.0)
CLAIM_SCOPE = (
    "One fixed auxiliary-overhead experiment on three frozen v2 families (anchor, injected, indirection): B "
    "analogue / C control / J Jev with and without a real auxiliary LLM note before every action decision. "
    "Descriptive only; not an ALFWorld/AndroidWorld reproduction and not an estimate of the paper's effect sizes."
)


def freeze_sha256() -> str:
    h = hashlib.sha256()
    for name in FREEZE_FILES:
        h.update(name.encode() + b"\0" + (HERE / name).read_bytes() + b"\0")
    return h.hexdigest()


def pins_intact() -> bool:
    return (v3run.v2_pin_intact() and v3run.FREEZE_SHA256 is not None
            and v3run.FREEZE_SHA256 == v3run.freeze_sha256())


def instances_for(phase: str) -> list[dict]:
    seeds = TEST_SEEDS if phase == "test" else SMOKE_SEEDS
    if phase == "test":
        assert not set(seeds) & USED_SEEDS, "v3b test seeds must be disjoint from every earlier run"
    return gen.generate(seeds, families=FAMILIES)


def expected_rows(phase: str) -> int:
    return len(instances_for(phase)) * len(ORDERS) * 2


def run_phase(selector, wrapper, arm, level, instances, pricing, progress=lambda m: None, checkpoint=None):
    rows, status = [], "COMPLETED"
    try:
        for i, wf in enumerate(instances):
            for order in ORDERS:
                for forced in (False, True):
                    row = core.run_episode_v2(wf, wrapper or selector, order, pricing, arm, forced_first=forced)
                    row |= (wrapper.drain() if wrapper else auxarms.zero_aux())
                    row["overhead"] = level
                    rows.append(row)
                    if checkpoint:
                        checkpoint(row)
            progress(f"{i + 1}/{len(instances)} instances ({wf['family']})")
    except v2arms.SpendCapReached as exc:
        status = "INCOMPLETE_SPEND_CAP"
        progress(f"STOP: {exc}")
    except KeyboardInterrupt:
        status = "INCOMPLETE_INTERRUPTED"
    except Exception as exc:  # noqa: BLE001 - recorded in the evidence status, never swallowed
        status = f"INCOMPLETE_ERROR:{type(exc).__name__}"
        progress(f"ERROR: {type(exc).__name__}")
    return rows, status


def build_evidence(arm, level, phase, rows, status, identity, spent, aux_spent, cap) -> dict:
    return {
        "experiment_id": EXPERIMENT_ID, "phase": phase, "arm": arm, "overhead": level, "status": status,
        "generator_version": gen.GENERATOR_VERSION, "families": list(FAMILIES), "arm_label": v3run.ARM_LABEL[arm],
        "freeze_sha256": freeze_sha256(), "v3a_freeze_sha256": v3run.freeze_sha256(),
        "v2_freeze_sha256": v2run.freeze_sha256(), "execution_environment": "local",
        "spend_usd": spent, "aux_spend_usd": aux_spent, "spend_cap_usd": cap,
        "aux_spend_cap_usd": AUX_CAP_USD if level == "O1" else 0.0, "expected_rows": expected_rows(phase),
        "identity": identity, "aggregate": v2run.aggregate(rows) if rows else None, "rows": rows,
        "claim_scope": CLAIM_SCOPE,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=ARMS, required=True)
    ap.add_argument("--overhead", choices=LEVELS, required=True)
    ap.add_argument("--phase", choices=("smoke", "test"), required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    keys = {v3run.KEY_ENV[args.arm]: os.environ.get(v3run.KEY_ENV[args.arm], "").strip()}
    if args.overhead == "O1":
        keys["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    missing = [k for k, v in keys.items() if not v]
    if missing:
        print(json.dumps({"experiment_id": EXPERIMENT_ID, "arm": args.arm, "overhead": args.overhead,
                          "status": "SKIPPED_NO_CREDENTIAL", "detail": f"{missing} not set; no API call, no evidence."},
                         indent=2))
        return 0
    if args.phase == "test" and (FREEZE_SHA256 is None or FREEZE_SHA256 != freeze_sha256() or not pins_intact()):
        print("REFUSED: test phase requires the pinned v3b freeze hash and intact v2 and v3a pins.", file=sys.stderr)
        return 4
    if args.phase == "smoke" and Path(args.out).resolve().is_relative_to((HERE.parent / "evidence").resolve()):
        print("REFUSED: smoke output must not be written into the evidence directory.", file=sys.stderr)
        return 6
    key = keys[v3run.KEY_ENV[args.arm]]
    pricing, cap = v3run.PRICING[args.arm], CELL_CAP_USD[args.arm]
    guard = v2arms.SpendGuard(cap, pricing)
    anthropic_client = None
    if args.arm != "jev" or args.overhead == "O1":
        try:
            import anthropic
        except ImportError:
            print("pip install 'anthropic>=1,<2' (optional extra: reproforge[control])", file=sys.stderr)
            return 5
        anthropic_client = anthropic.Anthropic(api_key=keys["ANTHROPIC_API_KEY"] if "ANTHROPIC_API_KEY" in keys else key,
                                               max_retries=0, timeout=60.0)
    if args.arm == "jev":
        client = v1.JevClient(v1.load_fixture()["api"], key)
        identity = v2run.jev_identity(client)
        selector = v2arms.JevArm(client, guard=guard)
    else:
        identity = v2run.control_identity(anthropic_client)
        selector = (v2arms.ControlArm if args.arm == "control" else v3arms.BArm)(anthropic_client, guard=guard)
    if identity.get("resolved_model") != v3run.RESOLVED[args.arm]:
        print(json.dumps({"status": "ABORTED_IDENTITY_FAILED", "identity_keys": sorted(identity)}), file=sys.stderr)
        return 3
    wrapper, aux_guard = None, v2arms.SpendGuard(AUX_CAP_USD, auxarms.AUX_PRICING)
    if args.overhead == "O1":
        aux_identity = v2run.control_identity(anthropic_client)
        if aux_identity.get("resolved_model") != auxarms.AUX_MODEL:
            print(json.dumps({"status": "ABORTED_AUX_IDENTITY_FAILED"}), file=sys.stderr)
            return 3
        identity["aux_identity"] = aux_identity
        wrapper = auxarms.AuxWrapped(selector, anthropic_client, guard=aux_guard)
    partial = Path(args.out + ".partial.jsonl")
    with partial.open("w") as fh:
        rows, status = run_phase(
            selector, wrapper, args.arm, args.overhead, instances_for(args.phase), pricing,
            progress=lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", file=sys.stderr, flush=True),
            checkpoint=lambda r: (fh.write(json.dumps(r) + "\n"), fh.flush()))
    evidence = build_evidence(args.arm, args.overhead, args.phase, rows, status, json.loads(json.dumps(identity)),
                              guard.spent, aux_guard.spent, cap)
    text = json.dumps(evidence, indent=2, sort_keys=True)
    if any(v in text for v in keys.values()):
        print("ABORT: credential value found in output; refusing to write.", file=sys.stderr)
        return 2
    Path(args.out).write_text(text + "\n")
    partial.unlink(missing_ok=True)
    print(json.dumps({"arm": args.arm, "overhead": args.overhead, "phase": args.phase, "status": status,
                      "rows": len(rows), "spend_usd": guard.spent, "aux_spend_usd": aux_guard.spent}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
