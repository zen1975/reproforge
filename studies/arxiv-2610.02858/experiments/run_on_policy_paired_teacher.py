"""On-policy paired-teacher data-generation analogue for HAD.

A Qwen2.5-0.5B student visits states in a deterministic toy interactive
environment. The same Qwen2.5-1.5B teacher then scores candidate actions twice
at each visited state: with harness information and without harness information.
This creates real model-backed HAD preference pairs without task rewards or
future information.
"""

from __future__ import annotations

import argparse
import gc
import json
import random

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 261002858

ENV = {
    "start": {
        "state": "A dirty mug is on the desk. You are holding nothing.",
        "actions": ["pick mug", "go sink", "wait"],
        "harness": "Admissible actions: pick mug / go sink. Held objects: none. Previous no-effect actions: wait.",
        "next": {"pick mug": "holding", "go sink": "sink_empty", "wait": "start"},
    },
    "holding": {
        "state": "The dirty mug is in your hand.",
        "actions": ["go sink", "put mug", "wait"],
        "harness": "Admissible actions: go sink / put mug. Held objects: mug. Previous no-effect actions: wait.",
        "next": {"go sink": "at_sink", "put mug": "start", "wait": "holding"},
    },
    "sink_empty": {
        "state": "You are at the sink but the mug is still on the desk.",
        "actions": ["go desk", "wash mug", "wait"],
        "harness": "Admissible actions: go desk. Held objects: none. Previous no-effect actions: wash mug / wait.",
        "next": {"go desk": "start", "wash mug": "sink_empty", "wait": "sink_empty"},
    },
    "at_sink": {
        "state": "You are at the sink holding the dirty mug.",
        "actions": ["wash mug", "put mug", "wait"],
        "harness": "Admissible actions: wash mug / put mug. Held objects: mug. Previous no-effect actions: wait.",
        "next": {"wash mug": "clean", "put mug": "sink_empty", "wait": "at_sink"},
    },
    "clean": {
        "state": "The mug is clean. Task complete.",
        "actions": ["stop"],
        "harness": "Admissible actions: stop. Held objects: mug. Previous no-effect actions: none.",
        "next": {"stop": "clean"},
    },
}


def action_mean_logprob(model, tokenizer, prompt, action):
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    action_ids = tokenizer(" " + action, add_special_tokens=False)["input_ids"]
    ids = torch.tensor([prompt_ids + action_ids], dtype=torch.long)
    logits = model(input_ids=ids).logits
    start = len(prompt_ids) - 1
    token_logits = logits[0, start : start + len(action_ids), :]
    targets = torch.tensor(action_ids, dtype=torch.long)
    log_probs = F.log_softmax(token_logits, dim=-1)
    return float(log_probs.gather(1, targets.unsqueeze(1)).squeeze(1).mean().item())


def choose(model, tokenizer, prompt, actions):
    scored = [
        {"action": action, "score": action_mean_logprob(model, tokenizer, prompt, action)}
        for action in actions
    ]
    scored.sort(key=lambda item: (-item["score"], item["action"]))
    return scored[0]["action"], scored


def load_model(model_id):
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    model.eval()
    return model, tok


def free(model, tokenizer):
    del model
    del tokenizer
    gc.collect()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--teacher-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    parser.add_argument("--max-steps", type=int, default=4)
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)

    student, student_tok = load_model(args.student_model)
    visited = []
    state_id = "start"
    for step in range(args.max_steps):
        row = ENV[state_id]
        prompt = (
            "You are an agent. Choose exactly one action from the candidates.\n"
            f"State: {row['state']}\n"
            f"Candidates: {' / '.join(row['actions'])}\n"
            "Action:"
        )
        action, scores = choose(student, student_tok, prompt, row["actions"])
        visited.append({
            "step": step + 1,
            "state_id": state_id,
            "state": row["state"],
            "actions": row["actions"],
            "harness": row["harness"],
            "student_action": action,
            "student_scores": scores,
        })
        state_id = row["next"][action]
        if state_id == "clean":
            break
    free(student, student_tok)

    teacher, teacher_tok = load_model(args.teacher_model)
    pairs = []
    for item in visited:
        actions = item["actions"]
        base = (
            "You are a teacher policy. Choose exactly one action from the candidates.\n"
            f"State: {item['state']}\n"
            f"Candidates: {' / '.join(actions)}\n"
        )
        with_prompt = base + f"Harness: {item['harness']}\nAction:"
        without_prompt = base + "Action:"
        positive, with_scores = choose(teacher, teacher_tok, with_prompt, actions)
        negative, without_scores = choose(teacher, teacher_tok, without_prompt, actions)

        admissible_text = item["harness"].split("Admissible actions:", 1)[1].split(".", 1)[0]
        admissible = {x.strip() for x in admissible_text.split("/")}
        no_effect = set()
        if "Previous no-effect actions:" in item["harness"]:
            part = item["harness"].split("Previous no-effect actions:", 1)[1].split(".", 1)[0].strip()
            if part != "none":
                no_effect = {x.strip() for x in part.split("/")}

        valid = positive in admissible and positive not in no_effect
        pairs.append({
            **item,
            "teacher_with_harness_action": positive,
            "teacher_without_harness_action": negative,
            "active_contrast": positive != negative,
            "positive_valid": valid,
            "teacher_with_harness_scores": with_scores,
            "teacher_without_harness_scores": without_scores,
        })
    free(teacher, teacher_tok)

    active = sum(int(x["active_contrast"]) for x in pairs)
    valid_active = sum(int(x["active_contrast"] and x["positive_valid"]) for x in pairs)
    student_progress = visited[-1]["state_id"] if visited else None

    print(json.dumps({
        "experiment_id": "had-on-policy-paired-teacher-qwen-v1",
        "seed": SEED,
        "student_model": args.student_model,
        "teacher_model": args.teacher_model,
        "environment": "reproforge-had-toy-interactive-v1",
        "student_visited_states": len(visited),
        "student_last_visited_state": student_progress,
        "pairs": pairs,
        "active_contrasts": active,
        "valid_active_contrasts": valid_active,
        "contrast_rate": active / len(pairs) if pairs else 0.0,
        "valid_active_rate": valid_active / len(pairs) if pairs else 0.0,
        "uses_task_reward": False,
        "uses_success_label_for_pair_construction": False,
        "uses_future_information_for_validity": False,
        "status": "ON_POLICY_PAIRED_TEACHER_PATH_EXECUTED",
        "boundary": (
            "Synthetic interactive environment with real Qwen student/teacher models. "
            "This verifies student-visited-state paired-teacher data generation, not "
            "ALFWorld/WebShop/ScienceWorld or paper-reported performance."
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
