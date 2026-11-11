"""OPST wrong-answer robustness analogue (paper Table 5c) on Qwen2.5-0.5B, CPU.

One process = one (method, p, seed) cell of opst-wrong-answer-robustness-qwen0.5b-v1:
    --method sft   cross-entropy on z after the solution prompt; evaluates the student
    --method opst  GKD-consistent skewed JSD between the student on its own sampled
                   continuation and an EMA teacher that also sees z; evaluates the
                   EMA teacher without z
Both methods see the same 64 questions and, at p=0.75, the same 48 corrupted z.

Other modes:
    --calibrate    base-model accuracy on the calibration split only (never held-out)
    --smoke        tiny random-init Qwen2 model + smoke split; checks the torch
                   divergence against opst_mechanism.d_alpha_consistent

Every value not published by the paper is listed in opst_wr_config_v1.json with
source "reproforge".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import random
import sys
import time
from pathlib import Path

import torch
import torch.nn.functional as F
from peft import LoraConfig, get_peft_model
from transformers import AutoModelForCausalLM, AutoTokenizer, Qwen2Config, Qwen2ForCausalLM

HERE = Path(__file__).resolve().parent
STUDY = HERE.parent
FIXTURE = STUDY / "fixtures" / "opst_wr_v1.json"
CONFIG = HERE / "opst_wr_config_v1.json"
sys.path.insert(0, str(HERE))

import opst_mechanism as m  # noqa: E402

LETTERS = "ABCD"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cfg(config: dict, key: str):
    return config["values"][key]["value"]


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------


def question_block(q: dict) -> str:
    lines = [f"Question: {q['question']}"]
    lines += [f"{letter}. {opt}" for letter, opt in zip(LETTERS, q["options"], strict=True)]
    return "\n".join(lines) + "\n"


def solution_prompt(q: dict) -> str:
    return question_block(q) + "Solution:"


def teacher_prompt(q: dict, z: str) -> str:
    return question_block(q) + f"Reference solution: {z}\n" + "Solution:"


def eval_prompt(q: dict) -> str:
    return question_block(q) + "Answer:"


# ---------------------------------------------------------------------------
# Objective
# ---------------------------------------------------------------------------


def skewed_jsd(student_logp: torch.Tensor, teacher_logq: torch.Tensor, alpha: float) -> torch.Tensor:
    """GKD-consistent D_alpha per position: q_bar = alpha q + (1 - alpha) p.

    D = alpha KL(q || q_bar) + (1 - alpha) KL(p || q_bar); inputs are log-probs
    over the vocabulary (last dim). Returns one value per position.
    """
    log_mix = torch.logsumexp(
        torch.stack([teacher_logq + math.log(alpha), student_logp + math.log(1.0 - alpha)]), dim=0
    )
    kl_q = (teacher_logq.exp() * (teacher_logq - log_mix)).sum(-1)
    kl_p = (student_logp.exp() * (student_logp - log_mix)).sum(-1)
    return alpha * kl_q + (1.0 - alpha) * kl_p


def parity_check(alpha: float) -> dict:
    """The torch objective must equal the frozen mechanism implementation."""
    rng = random.Random(7)
    max_err = 0.0
    printed_gap = 0.0
    for _ in range(20):
        p = [rng.random() + 1e-3 for _ in range(6)]
        q = [rng.random() + 1e-3 for _ in range(6)]
        p = [x / sum(p) for x in p]
        q = [x / sum(q) for x in q]
        t = skewed_jsd(torch.tensor(p, dtype=torch.float64).log(), torch.tensor(q, dtype=torch.float64).log(), alpha)
        max_err = max(max_err, abs(float(t) - m.d_alpha_consistent(p, q, alpha)))
        printed_gap = max(printed_gap, abs(float(t) - m.d_alpha_printed(p, q, alpha)))
    ok = max_err < 1e-10 and printed_gap > 1e-4
    if not ok:
        raise SystemExit(f"parity check failed: max_err={max_err} printed_gap={printed_gap}")
    return {"max_abs_error_vs_d_alpha_consistent": max_err, "max_abs_gap_vs_d_alpha_printed": printed_gap, "ok": ok}


# ---------------------------------------------------------------------------
# Model helpers
# ---------------------------------------------------------------------------


def letter_ids(tok) -> list[int]:
    ids = []
    for letter in LETTERS:
        enc = tok(" " + letter, add_special_tokens=False)["input_ids"]
        if len(enc) != 1:
            raise SystemExit(f"letter {letter!r} is not a single token: {enc}")
        ids.append(enc[0])
    return ids


@torch.no_grad()
def evaluate(model, tok, items: list[dict]) -> dict:
    """Closed-set log-likelihood over ' A'..' D' after 'Answer:'."""
    model.eval()
    lids = letter_ids(tok)
    gold_logp, correct = [], []
    for q in items:
        ids = torch.tensor([tok(eval_prompt(q))["input_ids"]])
        logits = model(input_ids=ids).logits[0, -1, lids].double()
        logp = torch.log_softmax(logits, dim=-1)
        g = LETTERS.index(q["gold"])
        gold_logp.append(float(logp[g]))
        correct.append(int(int(torch.argmax(logp)) == g))
    return {
        "n": len(items),
        "mean_gold_logprob": sum(gold_logp) / len(gold_logp),
        "accuracy": sum(correct) / len(correct),
        "per_item_gold_logprob": gold_logp,
    }


def lora_params(model) -> dict[str, torch.nn.Parameter]:
    return {n: p for n, p in model.named_parameters() if p.requires_grad}


class SwapIn:
    """Temporarily load EMA weights into the LoRA parameters."""

    def __init__(self, params: dict, weights: dict):
        self.params, self.weights, self.backup = params, weights, {}

    def __enter__(self):
        for n, p in self.params.items():
            self.backup[n] = p.data.clone()
            p.data.copy_(self.weights[n])

    def __exit__(self, *exc):
        for n, p in self.params.items():
            p.data.copy_(self.backup[n])


def ema_step(ema: dict, params: dict, beta: float) -> None:
    with torch.no_grad():
        for n, p in params.items():
            ema[n].mul_(1.0 - beta).add_(p.detach(), alpha=beta)


# ---------------------------------------------------------------------------
# Losses
# ---------------------------------------------------------------------------


def sft_loss(model, tok, batch: list[tuple[dict, str]]) -> torch.Tensor:
    per_sample = []
    for q, z in batch:
        prompt_ids = tok(solution_prompt(q))["input_ids"]
        target_ids = tok(" " + z, add_special_tokens=False)["input_ids"]
        ids = torch.tensor([prompt_ids + target_ids])
        logits = model(input_ids=ids).logits[0, len(prompt_ids) - 1 : -1]
        per_sample.append(F.cross_entropy(logits, torch.tensor(target_ids)))
    return torch.stack(per_sample).mean()


def rollout(model, tok, q: dict, max_new_tokens: int) -> list[int]:
    model.eval()
    prompt_ids = tok(solution_prompt(q), return_tensors="pt")["input_ids"]
    with torch.no_grad():
        out = model.generate(
            input_ids=prompt_ids,
            attention_mask=torch.ones_like(prompt_ids),
            do_sample=True,
            temperature=1.0,
            top_p=1.0,
            top_k=0,
            repetition_penalty=1.0,
            max_new_tokens=max_new_tokens,
            pad_token_id=tok.pad_token_id if tok.pad_token_id is not None else tok.eos_token_id,
        )
    y = out[0, prompt_ids.shape[1] :].tolist()
    if tok.eos_token_id in y:
        y = y[: y.index(tok.eos_token_id) + 1]
    return y


def opst_loss(model, tok, batch, params, ema, alpha, max_new_tokens, log_rollouts) -> torch.Tensor:
    rollouts = [(q, z, rollout(model, tok, q, max_new_tokens)) for q, z in batch]
    model.train()
    per_sample = []
    for q, z, y in rollouts:
        if not y:
            continue
        s_prompt = tok(solution_prompt(q))["input_ids"]
        t_prompt = tok(teacher_prompt(q, z))["input_ids"]
        with torch.no_grad(), SwapIn(params, ema):
            t_logits = model(input_ids=torch.tensor([t_prompt + y])).logits[0, len(t_prompt) - 1 : -1]
        s_logits = model(input_ids=torch.tensor([s_prompt + y])).logits[0, len(s_prompt) - 1 : -1]
        d = skewed_jsd(torch.log_softmax(s_logits.double(), -1), torch.log_softmax(t_logits.double(), -1), alpha)
        per_sample.append(d.mean())
        if len(log_rollouts) < 8:
            log_rollouts.append({"question": q["question"], "z": z, "rollout": tok.decode(y)})
    if not per_sample:
        raise SystemExit("all rollouts in a batch were empty")
    return torch.stack(per_sample).mean()


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def load(model_id: str, revision: str, smoke: bool):
    tok = AutoTokenizer.from_pretrained(model_id, revision=revision)
    if smoke:
        config = Qwen2Config(
            vocab_size=len(tok), hidden_size=32, intermediate_size=64, num_hidden_layers=2,
            num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=512,
            tie_word_embeddings=True,
        )
        model = Qwen2ForCausalLM(config).float()
    else:
        model = AutoModelForCausalLM.from_pretrained(model_id, revision=revision, dtype=torch.float32, low_cpu_mem_usage=True)
    return model, tok


def train_cell(args, config, fixture) -> dict:
    seed = 101 if args.smoke else args.seed
    random.seed(seed)
    torch.manual_seed(seed)
    model, tok = load(cfg(config, "model_id"), cfg(config, "model_revision"), args.smoke)
    resolved_revision = getattr(model.config, "_commit_hash", None)

    rows = fixture["train"][str(seed)]
    heldout = fixture["splits"]["smoke" if args.smoke else "heldout"]
    if args.smoke:
        rows = rows[:8]
    corrupt = args.p > 0
    if corrupt and abs(args.p - fixture["wrong_fraction"]) > 1e-9:
        raise SystemExit("only p in {0, fixture wrong_fraction} is pre-registered")
    data = [(r, r["z_wrong"] if corrupt and r["corrupt_at_p075"] else r["z_correct"]) for r in rows]
    train_gold = [{k: r[k] for k in ("question", "options", "gold")} for r in rows]

    before_heldout = evaluate(model, tok, heldout)
    before_train = evaluate(model, tok, train_gold)

    model = get_peft_model(model, LoraConfig(
        r=8, lora_alpha=16, lora_dropout=0.0,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM",
    ))
    params = lora_params(model)
    ema = {n: p.detach().clone() for n, p in params.items()}
    optimizer = torch.optim.AdamW(params.values(), lr=2e-4, weight_decay=0.0)
    alpha, beta = cfg(config, "alpha"), cfg(config, "ema_beta")
    batch_size = cfg(config, "batch_size")
    epochs = 1 if args.smoke else cfg(config, "epochs")
    max_new = 4 if args.smoke else cfg(config, "rollout_max_new_tokens")

    order_rng = random.Random(seed)
    losses, rollouts, steps, ema_updates = [], [], 0, 0
    start = time.time()
    for _ in range(epochs):
        order = list(range(len(data)))
        order_rng.shuffle(order)
        for i in range(0, len(order), batch_size):
            batch = [data[j] for j in order[i : i + batch_size]]
            if args.method == "sft":
                model.train()
                loss = sft_loss(model, tok, batch)
            else:
                loss = opst_loss(model, tok, batch, params, ema, alpha, max_new, rollouts)
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            steps += 1
            if args.method == "opst":
                ema_step(ema, params, beta)
                ema_updates += 1
            losses.append(loss.item())
    train_seconds = time.time() - start

    if args.method == "opst":
        with SwapIn(params, ema):
            after_heldout = evaluate(model, tok, heldout)
            after_train = evaluate(model, tok, train_gold)
        evaluated = "ema_teacher_without_z"
    else:
        after_heldout = evaluate(model, tok, heldout)
        after_train = evaluate(model, tok, train_gold)
        evaluated = "student"

    return {
        "mode": "smoke" if args.smoke else "frozen",
        "method": args.method,
        "p": args.p,
        "seed": seed,
        "resolved_model_revision": resolved_revision,
        "evaluated_model": evaluated,
        "gradient_steps": steps,
        "ema_updates": ema_updates,
        "corrupted_train_samples": sum(1 for r, z in data if z != r["z_correct"]),
        "train_losses": losses,
        "train_seconds": train_seconds,
        "rollout_examples": rollouts,
        "before": {"heldout": before_heldout, "train_gold": before_train},
        "after": {"heldout": after_heldout, "train_gold": after_train},
    }


def calibrate(config, fixture) -> dict:
    model, tok = load(cfg(config, "model_id"), cfg(config, "model_revision"), False)
    return {
        "mode": "calibrate",
        "resolved_model_revision": getattr(model.config, "_commit_hash", None),
        "calibration": evaluate(model, tok, fixture["splits"]["calibration"]),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--method", choices=["sft", "opst"])
    parser.add_argument("--p", type=float, default=0.0)
    parser.add_argument("--seed", type=int, choices=[101, 202, 303])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--calibrate", action="store_true")
    args = parser.parse_args()

    config = json.loads(CONFIG.read_text())
    fixture = json.loads(FIXTURE.read_text())
    torch.use_deterministic_algorithms(True, warn_only=True)
    header = {
        "evaluation_id": config["evaluation_id"],
        "hashes": {
            "runner_sha256": _sha256(Path(__file__)),
            "config_sha256": _sha256(CONFIG),
            "fixture_sha256": _sha256(FIXTURE),
            "mechanism_sha256": _sha256(HERE / "opst_mechanism.py"),
        },
        "environment": {
            "python": platform.python_version(),
            "torch": torch.__version__,
            "transformers": __import__("transformers").__version__,
            "peft": __import__("peft").__version__,
            "torch_threads": torch.get_num_threads(),
        },
        "parity": parity_check(cfg(config, "alpha")),
    }
    if args.calibrate:
        body = calibrate(config, fixture)
    else:
        if args.method is None or (args.seed is None and not args.smoke):
            parser.error("--method and --seed are required for a training cell")
        body = train_cell(args, config, fixture)
    json.dump({**header, **body}, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
