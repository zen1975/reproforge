"""Model-backed harness-signal contrast test for HAD.

The same Qwen2.5-1.5B teacher scores actions with and without harness-only
constraints at states actually acted on by a Qwen2.5-0.5B student. Scenarios are
chosen specifically to require harness-only failure/state information.
"""

from __future__ import annotations

import argparse
import gc
import json
import random

import torch
import torch.nn.functional as F
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 261002859

SCENARIOS = [
    {
        "id": "api-failure",
        "state": "A request to the primary API failed once. The task still needs to be completed.",
        "actions": ["retry primary API", "use cached backup", "stop"],
        "harness": "Admissible actions: use cached backup / stop. Previous no-effect actions: retry primary API.",
        "admissible": {"use cached backup", "stop"},
        "no_effect": {"retry primary API"},
    },
    {
        "id": "approval-required",
        "state": "An invoice is drafted and ready for the next operational action.",
        "actions": ["send invoice", "request approval", "discard invoice"],
        "harness": "Approval status: missing. Admissible actions: request approval / discard invoice.",
        "admissible": {"request approval", "discard invoice"},
        "no_effect": set(),
    },
    {
        "id": "missing-key",
        "state": "A locked door blocks the goal.",
        "actions": ["unlock door", "search for key", "leave"],
        "harness": "Held objects: none. Unlock requires key. Admissible actions: search for key / leave.",
        "admissible": {"search for key", "leave"},
        "no_effect": set(),
    },
    {
        "id": "stalled-search",
        "state": "The previous search did not find the needed answer. Work must continue.",
        "actions": ["search again", "open cached result", "answer now"],
        "harness": "Previous no-effect actions: search again. Admissible actions: open cached result / answer now.",
        "admissible": {"open cached result", "answer now"},
        "no_effect": {"search again"},
    },
]


def load(model_id):
    tok = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(model_id, dtype=torch.float32)
    model.eval()
    return model, tok


def score(model, tok, prompt, action):
    p = tok(prompt, add_special_tokens=True)["input_ids"]
    a = tok(" " + action, add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + a], dtype=torch.long)
    logits = model(input_ids=ids).logits
    start = len(p) - 1
    token_logits = logits[0, start : start + len(a), :]
    targets = torch.tensor(a, dtype=torch.long)
    logp = F.log_softmax(token_logits, dim=-1)
    return float(logp.gather(1, targets.unsqueeze(1)).squeeze(1).mean().item())


def choose(model, tok, prompt, actions):
    rows = [{"action": a, "score": score(model, tok, prompt, a)} for a in actions]
    rows.sort(key=lambda x: (-x["score"], x["action"]))
    return rows[0]["action"], rows


def free(model, tok):
    del model, tok
    gc.collect()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--student-model", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--teacher-model", default="Qwen/Qwen2.5-1.5B-Instruct")
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)

    student, student_tok = load(args.student_model)
    visited = []
    for row in SCENARIOS:
        base = (
            "You are an agent. Choose exactly one next action from the candidates.\n"
            f"State: {row['state']}\n"
            f"Candidates: {' / '.join(row['actions'])}\n"
            "Action:"
        )
        action, scores = choose(student, student_tok, base, row["actions"])
        visited.append({"scenario": row, "student_action": action, "student_scores": scores})
    free(student, student_tok)

    teacher, teacher_tok = load(args.teacher_model)
    pairs = []
    for visit in visited:
        row = visit["scenario"]
        base = (
            "You are a teacher policy. Choose exactly one next action from the candidates.\n"
            f"State: {row['state']}\n"
            f"Candidates: {' / '.join(row['actions'])}\n"
        )
        without_action, without_scores = choose(
            teacher, teacher_tok, base + "Action:", row["actions"]
        )
        with_action, with_scores = choose(
            teacher,
            teacher_tok,
            base + f"Harness-only records: {row['harness']}\nAction:",
            row["actions"],
        )
        valid = with_action in row["admissible"] and with_action not in row["no_effect"]
        pairs.append({
            "scenario_id": row["id"],
            "state": row["state"],
            "actions": row["actions"],
            "harness": row["harness"],
            "student_action": visit["student_action"],
            "student_scores": visit["student_scores"],
            "teacher_with_harness_action": with_action,
            "teacher_without_harness_action": without_action,
            "active_contrast": with_action != without_action,
            "positive_valid": valid,
            "teacher_with_harness_scores": with_scores,
            "teacher_without_harness_scores": without_scores,
        })
    free(teacher, teacher_tok)

    active = sum(int(x["active_contrast"]) for x in pairs)
    valid_active = sum(int(x["active_contrast"] and x["positive_valid"]) for x in pairs)
    harness_corrected_student = sum(
        int(x["teacher_with_harness_action"] != x["student_action"] and x["positive_valid"])
        for x in pairs
    )

    print(json.dumps({
        "experiment_id": "had-harness-signal-qwen-contrast-v2",
        "seed": SEED,
        "student_model": args.student_model,
        "teacher_model": args.teacher_model,
        "student_acted_states": len(pairs),
        "pairs": pairs,
        "active_contrasts": active,
        "valid_active_contrasts": valid_active,
        "contrast_rate": active / len(pairs),
        "valid_active_rate": valid_active / len(pairs),
        "harness_corrected_student_actions": harness_corrected_student,
        "uses_task_reward": False,
        "uses_success_label_for_pair_construction": False,
        "uses_future_information_for_validity": False,
        "status": "HARNESS_SIGNAL_CONTRAST_EXECUTED",
        "boundary": (
            "Synthetic harness-dependent states with real Qwen models. This tests whether "
            "harness-only records change same-teacher action preferences; it is not a "
            "paper benchmark or performance reproduction."
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
