"""Lightweight model-backed analogue for the FOCUS draft-plan path.

This validates that a real causal LM can be sampled stochastically, parsed into
span dependencies, and passed into the deterministic FOCUS core. It is not a
paper benchmark reproduction.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import random
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
CAP = ROOT / "capabilities" / "agent.decision-preserving-context-compressor"
SEED = 260937590


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prompt() -> str:
    return """You are a planning helper. Read the task and numbered history spans.
Return a short future plan. Every step MUST end with exactly:
Depends on: [s_X, s_Y]
Use only span IDs that appear below.
Then add one final line:
Rescued Spans: [s_X] | Reason: short reason
Use [] if no rescue is needed.

Task: send the final approved invoice to the customer without repeating a failed login.

History:
[s_1] Thought: need customer email | Action: lookup CRM | Observation: customer email is client@example.com
[s_2] Thought: login with old password | Action: authenticate | Observation: authentication failed; old password is invalid
[s_3] Thought: retrieve updated credential | Action: read secret store | Observation: use token NEW_TOKEN
[s_4] Thought: inspect invoice | Action: open invoice | Observation: invoice INV-42 is draft
[s_5] Thought: obtain approval | Action: read approval queue | Observation: INV-42 approved by finance
[s_6] Thought: inspect unrelated note | Action: open note | Observation: office lunch is Friday
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="HuggingFaceTB/SmolLM2-135M-Instruct")
    parser.add_argument("--rollouts", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-new-tokens", type=int, default=96)
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    model = AutoModelForCausalLM.from_pretrained(args.model_id)
    model.eval()

    parser_mod = _load(CAP / "parser.py", "focus_parser_model_backed")
    core_mod = _load(CAP / "compressor.py", "focus_core_model_backed")

    inputs = tokenizer(_prompt(), return_tensors="pt")
    outputs = []
    dependencies = []
    rescued_union = set()
    for index in range(args.rollouts):
        torch.manual_seed(SEED + index)
        with torch.no_grad():
            generated = model.generate(
                **inputs,
                do_sample=True,
                temperature=args.temperature,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )
        continuation = generated[0][inputs["input_ids"].shape[1]:]
        text = tokenizer.decode(continuation, skip_special_tokens=True)
        try:
            deps, rescued = parser_mod.parse_plan(text)
            parse_ok = True
            error = None
        except ValueError as exc:
            deps, rescued = set(), set()
            parse_ok = False
            error = str(exc)
        outputs.append({
            "rollout":index,
            "text":text,
            "parse_ok":parse_ok,
            "dependencies":sorted(deps),
            "rescued":sorted(rescued),
            "parse_error":error,
        })
        dependencies.append(deps)
        rescued_union |= rescued

    spans = [
        core_mod.Span(f"s_{i}", f"reason-{i}", f"action-{i}", f"observation-{i}")
        for i in range(1, 7)
    ]
    compression = core_mod.compress(
        spans,
        dependencies,
        tau=0.3,
        rescued_ids=rescued_union,
    )
    parse_successes = sum(int(item["parse_ok"]) for item in outputs)
    result = {
        "experiment_id":"focus-smollm-draft-analogue-v1",
        "model_id":args.model_id,
        "seed":SEED,
        "rollouts":args.rollouts,
        "temperature":args.temperature,
        "max_new_tokens":args.max_new_tokens,
        "parse_successes":parse_successes,
        "parse_success_rate":parse_successes / args.rollouts,
        "outputs":outputs,
        "compression":{
            "retained_ids":list(compression.retained_ids),
            "dropped_ids":list(compression.dropped_ids),
            "utility":compression.utility,
            "rescued_ids":list(compression.rescued_ids),
        },
        "status":"MODEL_BACKED_PATH_EXECUTED",
        "boundary":"Small public 135M model analogue on a synthetic trace. This validates the model->parser->FOCUS-core path only and is not evidence for paper benchmark quality."
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
