"""Qwen2.5-0.5B LoRA smoke for Harness-Aware Distillation.

This is a lightweight synthetic analogue. It executes the paper's action-only
pairwise preference loss and per-update gradient-norm balancing on a real small
causal LM, but it does not reproduce ALFWorld/WebShop/ScienceWorld.
"""

from __future__ import annotations

import argparse
import json
import math
import random

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 261002858

TRAIN = [
    {
        "prompt": "State: plate is dirty; holding plate. Harness: admissible actions are go sink / go cabinet. Reasoning: use harness feedback. Action:",
        "positive": " go sink",
        "negative": " go cabinet",
        "valid": True,
    },
    {
        "prompt": "State: item not in hand. Harness: admissible actions are pick cup / go shelf. Reasoning: use harness feedback. Action:",
        "positive": " pick cup",
        "negative": " go shelf",
        "valid": True,
    },
    {
        "prompt": "State: search made no progress. Harness: repeat search had no effect; admissible actions are open result / search. Reasoning: use harness feedback. Action:",
        "positive": " open result",
        "negative": " search",
        "valid": True,
    },
    {
        "prompt": "State: box closed; holding key. Harness: admissible actions are unlock box / leave room. Reasoning: use harness feedback. Action:",
        "positive": " unlock box",
        "negative": " leave room",
        "valid": True,
    },
    {
        "prompt": "State: invoice approved. Harness: admissible actions are send invoice / request approval. Reasoning: use harness feedback. Action:",
        "positive": " send invoice",
        "negative": " request approval",
        "valid": True,
    },
    {
        "prompt": "State: holding nothing. Harness: admissible actions are go sink / put plate. Reasoning: use harness feedback. Action:",
        "positive": " put plate",
        "negative": " go sink",
        "valid": False,
    },
]

TEST = [
    {
        "prompt": "State: mug is dirty; holding mug. Harness: admissible actions are go sink / go cabinet. Reasoning: use harness feedback. Action:",
        "positive": " go sink",
        "negative": " go cabinet",
    },
    {
        "prompt": "State: report approved. Harness: admissible actions are send report / request approval. Reasoning: use harness feedback. Action:",
        "positive": " send report",
        "negative": " request approval",
    },
    {
        "prompt": "State: repeated lookup had no effect. Harness: admissible actions are open cache / lookup. Reasoning: use harness feedback. Action:",
        "positive": " open cache",
        "negative": " lookup",
    },
    {
        "prompt": "State: door locked; holding key. Harness: admissible actions are unlock door / leave. Reasoning: use harness feedback. Action:",
        "positive": " unlock door",
        "negative": " leave",
    },
]


def action_mean_logprob(model, tokenizer, prompt: str, action: str):
    prompt_ids = tokenizer(prompt, add_special_tokens=True)["input_ids"]
    action_ids = tokenizer(action, add_special_tokens=False)["input_ids"]
    if not action_ids:
        raise ValueError("action tokenization is empty")
    ids = torch.tensor([prompt_ids + action_ids], dtype=torch.long)
    attention = torch.ones_like(ids)
    logits = model(input_ids=ids, attention_mask=attention).logits
    start = len(prompt_ids) - 1
    token_logits = logits[0, start : start + len(action_ids), :]
    targets = torch.tensor(action_ids, dtype=torch.long)
    log_probs = F.log_softmax(token_logits, dim=-1)
    selected = log_probs.gather(1, targets.unsqueeze(1)).squeeze(1)
    return selected.mean()


def grad_norm(loss, params, retain_graph=True):
    grads = torch.autograd.grad(
        loss,
        params,
        retain_graph=retain_graph,
        allow_unused=True,
    )
    total = torch.zeros((), dtype=torch.float32)
    for grad in grads:
        if grad is not None:
            total = total + grad.detach().float().pow(2).sum()
    return total.sqrt()


def evaluate(model, tokenizer):
    rows = []
    correct = 0
    margins = []
    model.eval()
    with torch.no_grad():
        for row in TEST:
            pos = action_mean_logprob(model, tokenizer, row["prompt"], row["positive"])
            neg = action_mean_logprob(model, tokenizer, row["prompt"], row["negative"])
            margin = float((pos - neg).item())
            margins.append(margin)
            ok = margin > 0
            correct += int(ok)
            rows.append({"positive": row["positive"], "negative": row["negative"], "margin": margin, "correct": ok})
    model.train()
    return {
        "accuracy": correct / len(TEST),
        "mean_margin": sum(margins) / len(margins),
        "rows": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="Qwen/Qwen2.5-0.5B-Instruct")
    parser.add_argument("--mode", choices=["distill-only", "had"], required=True)
    parser.add_argument("--steps", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--beta", type=float, default=0.5)
    parser.add_argument("--rho", type=float, default=0.5)
    parser.add_argument("--lora-r", type=int, default=4)
    parser.add_argument("--lora-alpha", type=int, default=8)\n    parser.add_argument("--version", default="v1")
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    base = AutoModelForCausalLM.from_pretrained(
        args.model_id,
        torch_dtype=torch.float32,
    )
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules=["q_proj", "v_proj"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(base, lora)
    model.train()
    params = [p for p in model.parameters() if p.requires_grad]
    optimizer = torch.optim.AdamW(
        params,
        lr=args.learning_rate,
        weight_decay=0.01,
    )

    before = evaluate(model, tokenizer)
    history = []
    for step in range(args.steps):
        row = TRAIN[step % len(TRAIN)]
        optimizer.zero_grad(set_to_none=True)

        pos = action_mean_logprob(model, tokenizer, row["prompt"], row["positive"])
        dist_loss = -pos

        neg = action_mean_logprob(model, tokenizer, row["prompt"], row["negative"])
        delta = pos - neg
        pref_loss = -F.logsigmoid(args.beta * delta)
        if not row["valid"]:
            pref_loss = pref_loss * 0.0

        if args.mode == "had":
            d_norm = grad_norm(dist_loss, params, retain_graph=True)
            p_norm = grad_norm(pref_loss, params, retain_graph=True)
            if float(p_norm.item()) == 0.0:
                lam = 0.0
            else:
                lam = float((args.rho * d_norm / p_norm).detach().item())
            loss = dist_loss + lam * pref_loss
        else:
            d_norm = grad_norm(dist_loss, params, retain_graph=True)
            p_norm = torch.zeros_like(d_norm)
            lam = 0.0
            loss = dist_loss

        loss.backward()
        torch.nn.utils.clip_grad_norm_(params, 1.0)
        optimizer.step()

        history.append({
            "step": step + 1,
            "valid_preference": row["valid"],
            "distillation_loss": float(dist_loss.detach().item()),
            "preference_loss": float(pref_loss.detach().item()),
            "distillation_grad_norm": float(d_norm.item()),
            "preference_grad_norm": float(p_norm.item()),
            "lambda": lam,
            "combined_loss": float(loss.detach().item()),
        })

    after = evaluate(model, tokenizer)
    trainable = sum(p.numel() for p in params)
    total = sum(p.numel() for p in model.parameters())

    print(json.dumps({
        "experiment_id": f"had-qwen0.5b-{args.mode}-smoke-{args.version}",
        "model_id": args.model_id,
        "mode": args.mode,
        "seed": SEED,
        "steps": args.steps,
        "learning_rate": args.learning_rate,
        "beta": args.beta,
        "rho": args.rho,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_fraction": trainable / total,
        "before": before,
        "after": after,
        "history": history,
        "status": "MODEL_BACKED_TRAINING_PATH_EXECUTED",
        "boundary": (
            "Synthetic Qwen2.5-0.5B LoRA smoke only. The paper uses different "
            "students/teachers, full fine-tuning, on-policy benchmark rollouts, "
            "and many more updates. This does not reproduce paper benchmark gains."
        ),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
