"""Multi-seed 0.5B student training from real model-generated HAD pairs.

Training pairs come only from active, valid contrasts observed in
had-harness-signal-qwen-contrast-v2 using the same Qwen2.5-1.5B teacher with and
without harness records. Evaluation states are new and frozen in this version.
"""

from __future__ import annotations

import argparse
import json
import random

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

TRAIN = [
    {
        "source_scenario": "api-failure",
        "prompt": (
            "State: A request to the primary API failed once. The task still needs to be completed.\n"
            "Harness-only records: Admissible actions: use cached backup / stop. "
            "Previous no-effect actions: retry primary API.\n"
            "Candidates: retry primary API / use cached backup / stop\nAction:"
        ),
        "positive": "use cached backup",
        "negative": "retry primary API",
    },
    {
        "source_scenario": "approval-required",
        "prompt": (
            "State: An invoice is drafted and ready for the next operational action.\n"
            "Harness-only records: Approval status: missing. "
            "Admissible actions: request approval / discard invoice.\n"
            "Candidates: send invoice / request approval / discard invoice\nAction:"
        ),
        "positive": "request approval",
        "negative": "send invoice",
    },
]

HELDOUT = [
    {
        "id": "fallback-endpoint",
        "prompt": (
            "State: The main service endpoint has just failed and the request must still complete.\n"
            "Harness-only records: Main endpoint retry is known no-effect. "
            "Admissible actions: use fallback endpoint / stop.\n"
            "Candidates: retry main endpoint / use fallback endpoint / stop\nAction:"
        ),
        "positive": "use fallback endpoint",
        "negative": "retry main endpoint",
    },
    {
        "id": "change-review",
        "prompt": (
            "State: A production change is prepared for the next operational action.\n"
            "Harness-only records: Required review is missing. "
            "Admissible actions: request review / discard change.\n"
            "Candidates: deploy change / request review / discard change\nAction:"
        ),
        "positive": "request review",
        "negative": "deploy change",
    },
    {
        "id": "payment-approval",
        "prompt": (
            "State: A payment instruction is drafted and ready.\n"
            "Harness-only records: Authorization is missing. "
            "Admissible actions: request authorization / cancel payment.\n"
            "Candidates: send payment / request authorization / cancel payment\nAction:"
        ),
        "positive": "request authorization",
        "negative": "send payment",
    },
    {
        "id": "stalled-fetch",
        "prompt": (
            "State: A fetch attempt failed to return the required record.\n"
            "Harness-only records: Repeating fetch is known no-effect. "
            "Admissible actions: open cached record / stop.\n"
            "Candidates: fetch again / open cached record / stop\nAction:"
        ),
        "positive": "open cached record",
        "negative": "fetch again",
    },
]


def action_logprob(model, tok, prompt, action):
    p = tok(prompt, add_special_tokens=True)["input_ids"]
    a = tok(" " + action, add_special_tokens=False)["input_ids"]
    ids = torch.tensor([p + a], dtype=torch.long)
    logits = model(input_ids=ids).logits
    start = len(p) - 1
    token_logits = logits[0, start : start + len(a), :]
    targets = torch.tensor(a, dtype=torch.long)
    logp = F.log_softmax(token_logits, dim=-1)
    return logp.gather(1, targets.unsqueeze(1)).squeeze(1).mean()


def grad_norm(loss, params):
    grads = torch.autograd.grad(loss, params, retain_graph=True, allow_unused=True)
    total = torch.zeros((), dtype=torch.float32)
    for grad in grads:
        if grad is not None:
            total = total + grad.detach().float().pow(2).sum()
    return total.sqrt()


def evaluate(model, tok):
    rows = []
    margins = []
    model.eval()
    with torch.no_grad():
        for row in HELDOUT:
            pos = action_logprob(model, tok, row["prompt"], row["positive"])
            neg = action_logprob(model, tok, row["prompt"], row["negative"])
            margin = float((pos - neg).item())
            margins.append(margin)
            rows.append({"id": row["id"], "margin": margin, "correct": margin > 0})
    model.train()
    return {
        "accuracy": sum(int(r["correct"]) for r in rows) / len(rows),
        "mean_margin": sum(margins) / len(margins),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--mode", choices=["distill-only", "had"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--steps", type=int, default=8)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--rho", type=float, default=0.5)
    args = parser.parse_args()

    random.seed(args.seed)
    torch.manual_seed(args.seed)

    tok = AutoTokenizer.from_pretrained(args.model_id)
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    base = AutoModelForCausalLM.from_pretrained(args.model_id, dtype=torch.float32)
    model = get_peft_model(base, LoraConfig(
        r=4,
        lora_alpha=8,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    ))
    model.train()
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(params, lr=args.learning_rate, weight_decay=0.01)

    before = evaluate(model, tok)
    history = []
    order = list(range(len(TRAIN)))
    for step in range(args.steps):
        if step % len(TRAIN) == 0:
            random.shuffle(order)
        row = TRAIN[order[step % len(TRAIN)]]
        optimizer.zero_grad(set_to_none=True)

        pos = action_logprob(model, tok, row["prompt"], row["positive"])
        neg = action_logprob(model, tok, row["prompt"], row["negative"])
        dist_loss = -pos
        pref_loss = -F.logsigmoid(args.beta * (pos - neg))

        d_norm = grad_norm(dist_loss, params)
        if args.mode == "had":
            p_norm = grad_norm(pref_loss, params)
            lam = 0.0 if float(p_norm.item()) == 0.0 else float(
                (args.rho * d_norm / p_norm).detach().item()
            )
            loss = dist_loss + lam * pref_loss
        else:
            p_norm = torch.zeros_like(d_norm)
            lam = 0.0
            loss = dist_loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        optimizer.step()
        history.append({
            "step": step + 1,
            "source_scenario": row["source_scenario"],
            "distillation_loss": float(dist_loss.detach().item()),
            "preference_loss": float(pref_loss.detach().item()),
            "distillation_grad_norm": float(d_norm.item()),
            "preference_grad_norm": float(p_norm.item()),
            "lambda": lam,
        })

    after = evaluate(model, tok)
    print(json.dumps({
        "experiment_id": f"had-real-pairs-{args.mode}-seed{args.seed}-v1",
        "source_pair_experiment": "had-harness-signal-qwen-contrast-v2",
        "model_id": args.model_id,
        "mode": args.mode,
        "seed": args.seed,
        "steps": args.steps,
        "train_pairs": 2,
        "heldout_examples": len(HELDOUT),
        "beta": args.beta,
        "rho": args.rho,
        "before": before,
        "after": after,
        "accuracy_change": after["accuracy"] - before["accuracy"],
        "mean_margin_change": after["mean_margin"] - before["mean_margin"],
        "history": history,
        "status": "REAL_TEACHER_PAIR_STUDENT_TRAINING_EXECUTED",
        "boundary": (
            "Training uses two active valid synthetic preference pairs actually generated "
            "by the Qwen2.5-1.5B same-teacher contrast run. Held-out states are unseen "
            "synthetic analogues. This is not paper benchmark reproduction."
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
