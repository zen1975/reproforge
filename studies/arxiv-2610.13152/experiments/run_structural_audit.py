"""Independent, partial, CPU-only structural trajectory mechanism audit.

Not the authors' TQS implementation. Only four published component equations
are reconstructed; no full composite score or author benchmark is claimed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import platform
import sys

ACTIONS = {"think", "read_file", "write_file", "execute_bash", "search", "submit", "other"}


def shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c/n)*math.log2(c/n) for c in counts.values())


def observation_entropy_collapse(steps: list[dict]) -> float | None:
    """OEC analogue: character entropy and trailing 3-step mean.

    For zero opening entropy return undefined rather than divide by zero.
    """
    h = [shannon_entropy(str(s.get("observation", ""))) for s in steps]
    if not h:
        return None
    opening = sum(h[:5])/min(5, len(h))
    if opening <= 0:
        return None
    moving = [sum(h[max(0,i-2):i+1]) / (i-max(0,i-2)+1) for i in range(len(h))]
    return max(0.0, min(1.0, 1.0-min(moving)/opening))


def tool_transition_entropy(steps: list[dict]) -> float | None:
    """Published TTE: entropy of 49 ordered pairs, normalized by log2(49)."""
    if len(steps) < 2:
        return None
    acts = [s["action"] for s in steps]
    if any(a not in ACTIONS for a in acts):
        raise ValueError("unknown action")
    pairs = Counter(zip(acts, acts[1:]))
    total = len(acts)-1
    return -sum((v/total)*math.log2(v/total) for v in pairs.values())/math.log2(49)


def solution_commitment_point(steps: list[dict]) -> float:
    """Published SCP; zero-based step t*; error flags supplied explicitly."""
    n = len(steps)
    for i,s in enumerate(steps):
        if s["action"] == "write_file" and not s.get("error", False):
            u = i/n
            d = max(0.0, 0.2-u, u-0.5)
            return math.exp(-(d*d)/(2*0.2*0.2))
    return 0.0


def post_error_diversity(steps: list[dict]) -> float | None:
    """Published PED; empty file-set Jaccard distance is defined as 0."""
    terms = []
    for i,s in enumerate(steps[:-1]):
        if not s.get("error", False):
            continue
        t = steps[i+1]
        a,b = set(s.get("files",[])), set(t.get("files",[]))
        union = a|b
        distance = 1.0-len(a&b)/len(union) if union else 0.0
        terms.append(0.5*(float(s["action"]!=t["action"])+distance))
    return sum(terms)/len(terms) if terms else None


def features(steps: list[dict]) -> dict:
    if len(steps)<3:
        raise ValueError("minimum 3 steps")
    if any(s.get("action") not in ACTIONS for s in steps):
        raise ValueError("unknown action")
    return {"OEC":observation_entropy_collapse(steps),"TTE":tool_transition_entropy(steps),"SCP":solution_commitment_point(steps),"PED":post_error_diversity(steps)}


def step(action,obs,files=(),error=False):
    return {"action":action,"observation":obs,"files":list(files),"error":error}


def fixtures() -> dict[str,list[dict]]:
    clean = [
        step("read_file","module alpha beta gamma",["a.py"]),
        step("search","matches found in alpha beta",["a.py","b.py"]),
        step("read_file","stack trace location",["b.py"]),
        step("execute_bash","error: test fails",["b.py"],True),
        step("read_file","focused line",["b.py"]),
        step("write_file","patch applied",["b.py"]),
        step("execute_bash","test passes",["b.py"]),
        step("read_file","review diff",["b.py"]),
        step("execute_bash","test passes",["b.py"]),
        step("write_file","cleanup applied",["b.py"]),
        step("execute_bash","all tests pass",["b.py"]),
        step("submit","complete",["b.py"]),
    ]
    loop = [step("execute_bash","error: test fails",["b.py"],True) for _ in range(12)]
    return {"clean":clean,"loop":loop}


def audit() -> dict:
    f=fixtures()
    rows={k:features(v) for k,v in f.items()}
    # A length-only baseline cannot distinguish the two equal-length traces.
    assertions={
      "same_length_baseline_tie":len(f["clean"])==len(f["loop"]),
      "TTE_separates_loop":rows["clean"]["TTE"]>rows["loop"]["TTE"],
      "SCP_detects_no_edit":rows["clean"]["SCP"]>rows["loop"]["SCP"],
      "PED_detects_failed_repetition":rows["clean"]["PED"]>rows["loop"]["PED"],
      "OEC_is_bounded":all(v["OEC"] is None or 0<=v["OEC"]<=1 for v in rows.values()),
      "all_features_bounded":all(v is None or 0<=v<=1 for row in rows.values() for v in row.values()),
    }
    if not all(assertions.values()):
        raise AssertionError(assertions)
    canonical=json.dumps(f,sort_keys=True,separators=(",",":"))
    return {"experiment_id":"tqs-structural-components-synthetic-v1","source_arxiv":"2610.13152",
      "experiment_kind":"independent_synthetic_mechanism_test","paper_reproduced":False,
      "claim_scope":"Published TTE, SCP, PED equations and OEC analogue; not full TQS, no training/held-out corpus",
      "seed":20261013,"fixture_sha256":hashlib.sha256(canonical.encode()).hexdigest(),
      "source_sha256":hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
      "environment":{"python":platform.python_version(),"platform":platform.system()+" "+platform.machine(),"dependencies":"Python standard library only"},
      "fixtures":{"trace_count":2,"steps_per_trace":12,"baseline_step_count":{"clean":12,"loop":12}},
      "features":rows,"assertions":assertions,"assertions_passed":sum(assertions.values()),
      "assertions_total":len(assertions),"limitations":["No public corpus processed", "No author implementation copied", "No TQS composite or IAC/PSN/DPI", "OEC initial-window convention is an independent analogue", "No training or paper-level accuracy reproduction", "Frozen after first observation; do not tune against these fixtures"]}


def main():
    ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path);args=ap.parse_args()
    result=audit();out=json.dumps(result,indent=2,sort_keys=True)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(out)
    print(out)

if __name__=="__main__":main()
