"""Generic LoRA SFT harness for paper-aligned task-tool training.

Defaults mirror the paper's published SFT hyperparameters where known.
Use --max-steps for inexpensive harness validation. Exact Gemma execution still
requires official model access and GPU resources.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

import torch
from peft import LoraConfig, get_peft_model
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForCausalLM, AutoTokenizer

SEED = 261003213


class ResponseOnlyDataset(Dataset):
    def __init__(self, rows, tokenizer, max_length):
        self.items = []
        for row in rows:
            prompt_ids = tokenizer(
                row["prompt"],
                add_special_tokens=True,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            full = tokenizer(
                row["prompt"] + row["completion"],
                add_special_tokens=True,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            labels = [-100] * min(len(prompt_ids), len(full)) + full[len(prompt_ids):]
            self.items.append({"input_ids": full, "labels": labels})

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        return self.items[idx]


def collate(batch, pad_token_id):
    max_len = max(len(item["input_ids"]) for item in batch)
    input_ids = []
    labels = []
    attention_mask = []
    for item in batch:
        pad = max_len - len(item["input_ids"])
        input_ids.append(item["input_ids"] + [pad_token_id] * pad)
        labels.append(item["labels"] + [-100] * pad)
        attention_mask.append([1] * len(item["input_ids"]) + [0] * pad)
    return {
        "input_ids": torch.tensor(input_ids, dtype=torch.long),
        "attention_mask": torch.tensor(attention_mask, dtype=torch.long),
        "labels": torch.tensor(labels, dtype=torch.long),
    }


def read_jsonl(path, limit=None):
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return rows[:limit] if limit else rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", required=True)
    parser.add_argument("--train-jsonl", required=True)
    parser.add_argument("--max-train-examples", type=int)
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--learning-rate", type=float, default=1.9e-4)
    parser.add_argument("--warmup-fraction", type=float, default=0.1)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--gradient-accumulation", type=int, default=16)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--lora-r", type=int, default=32)
    parser.add_argument("--lora-alpha", type=int, default=64)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--dtype", choices=["float32", "bfloat16"], default="float32")
    args = parser.parse_args()

    random.seed(SEED)
    torch.manual_seed(SEED)
    rows = read_jsonl(args.train_jsonl, args.max_train_examples)
    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.bfloat16 if args.dtype == "bfloat16" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(args.model_id, torch_dtype=dtype)
    lora = LoraConfig(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        target_modules="all-linear",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora)
    model.train()

    dataset = ResponseOnlyDataset(rows, tokenizer, args.max_length)
    loader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        shuffle=True,
        generator=torch.Generator().manual_seed(SEED),
        collate_fn=lambda batch: collate(batch, tokenizer.pad_token_id),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    steps_per_epoch = math.ceil(len(loader) / args.gradient_accumulation)
    total_steps = args.epochs * steps_per_epoch
    if args.max_steps is not None:
        total_steps = min(total_steps, args.max_steps)
    warmup_steps = max(1, int(total_steps * args.warmup_fraction)) if total_steps else 0

    def lr_scale(step):
        if warmup_steps and step < warmup_steps:
            return (step + 1) / warmup_steps
        return 1.0

    losses = []
    optimizer.zero_grad(set_to_none=True)
    update_step = 0
    for _epoch in range(args.epochs):
        for batch_index, batch in enumerate(loader, start=1):
            output = model(**batch)
            loss = output.loss / args.gradient_accumulation
            loss.backward()
            if batch_index % args.gradient_accumulation == 0 or batch_index == len(loader):
                scale = lr_scale(update_step)
                for group in optimizer.param_groups:
                    group["lr"] = args.learning_rate * scale
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
                losses.append(float(loss.item() * args.gradient_accumulation))
                update_step += 1
                if args.max_steps is not None and update_step >= args.max_steps:
                    break
        if args.max_steps is not None and update_step >= args.max_steps:
            break

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    result = {
        "model_id": args.model_id,
        "seed": SEED,
        "examples": len(rows),
        "epochs_requested": args.epochs,
        "optimizer_steps": update_step,
        "lora_r": args.lora_r,
        "lora_alpha": args.lora_alpha,
        "learning_rate_peak": args.learning_rate,
        "warmup_fraction": args.warmup_fraction,
        "max_length": args.max_length,
        "trainable_parameters": trainable,
        "total_parameters": total,
        "trainable_fraction": trainable / total,
        "first_loss": losses[0] if losses else None,
        "last_loss": losses[-1] if losses else None,
        "status": "HARNESS_EXECUTED",
        "boundary": (
            "Harness validation only unless model/data/hardware exactly match the paper. "
            "Prompt tokens are masked from the causal LM loss."
        ),
    }
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
