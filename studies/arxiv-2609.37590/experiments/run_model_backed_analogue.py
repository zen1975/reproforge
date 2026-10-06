"""Lightweight model-backed analogue for the FOCUS draft-plan path.

This executes the paper-shaped draft prompt with a small public model, parses
dependency citations strictly, and feeds them into the deterministic FOCUS core.
It is not a reproduction of the paper's GPT-4.1/Qwen3/Phi benchmark runs.
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

PAPER_SYSTEM_PROMPT = """You are a planning assistant performing Dual-Objective Defensive Drafting.
Given a partially completed task and the executor's workspace trace, your goal is twofold:
1. OPTIMISTIC PLANNING: Generate a high-level plan sketch for completion. For each step, cite the exact historical spans you depend on.
Format: Step: <description> | Depends on: [s_X, s_Y]
2. PESSIMISTIC VERIFICATION: Review all remaining, un-cited spans in the trace. If discarding an un-cited span would cause the executing agent to blindly repeat a mistake or lose causal state, you MUST rescue it.
Format: Rescued Spans: [s_A, s_B] | Reason: <risk if deleted>"""

TASK_AND_TRACE = """Task: send the final approved invoice to the customer without repeating a failed login.

Workspace trace:
[s_1] | Thought: need customer email | Action: lookup CRM | Observation: customer email is client@example.com
[s_2] | Thought: login with old password | Action: authenticate | Observation: authentication failed; old password is invalid
[s_3] | Thought: retrieve updated credential | Action: read secret store | Observation: use token NEW_TOKEN
[s_4] | Thought: inspect invoice | Action: open invoice | Observation: invoice INV-42 is draft
[s_5] | Thought: obtain approval | Action: read approval queue | Observation: INV-42 approved by finance
[s_6] | Thought: inspect unrelated note | Action: open note | Observation: office lunch is Friday
"""

REQUIRED_KEEP = {"s_1", "s_2", "s_3", "s_5"}
DISTRACTOR = "s_6"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--rollouts", type=int, default=3)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--max-new-tokens", type=int, default=256)
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    model = AutoModelForCausalLM.from_pretrained(args.model_id)
    model.eval()

    parser_mod = _load(CAP / "parser.py", "focus_parser_model_backed")
    core_mod = _load(CAP / "compressor.py", "focus_core_model_backed")

    messages = [
        {"role": "system", "content": PAPER_SYSTEM_PROMPT},
        {"role": "user", "content": TASK_AND_TRACE},
    ]
    if getattr(tokenizer, "chat_template", None):
        rendered = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
        )
    else:
        rendered = PAPER_SYSTEM_PROMPT + "\n\n" + TASK_AND_TRACE

    inputs = tokenizer(rendered, return_tensors="pt")
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

        outputs.append(
            {
                "rollout": index,
                "text": text,
                "parse_ok": parse_ok,
                "dependencies": sorted(deps),
                "rescued": sorted(rescued),
                "parse_error": error,
            }
        )
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
    retained = set(compression.retained_ids)
    required_preserved = REQUIRED_KEEP.issubset(retained)
    distractor_pruned = DISTRACTOR not in retained

    result = {
        "experiment_id": "focus-qwen0.5b-draft-analogue-v1",
        "model_id": args.model_id,
        "seed": SEED,
        "rollouts": args.rollouts,
        "temperature": args.temperature,
        "tau": 0.3,
        "max_new_tokens": args.max_new_tokens,
        "paper_prompt_shape": True,
        "parse_successes": parse_successes,
        "parse_success_rate": parse_successes / args.rollouts,
        "outputs": outputs,
        "compression": {
            "retained_ids": list(compression.retained_ids),
            "dropped_ids": list(compression.dropped_ids),
            "utility": compression.utility,
            "rescued_ids": list(compression.rescued_ids),
        },
        "required_keep_ids": sorted(REQUIRED_KEEP),
        "required_preserved": required_preserved,
        "distractor_id": DISTRACTOR,
        "distractor_pruned": distractor_pruned,
        "status": "MODEL_BACKED_PATH_EXECUTED",
        "boundary": (
            "Small public 0.5B model analogue on a synthetic trace using the paper-shaped "
            "draft format. This validates the model->parser->FOCUS-core path only and "
            "does not reproduce paper benchmark quality or GPT-4.1/Qwen3/Phi behavior."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
