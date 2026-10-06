"""Re-train the frozen specialization recipe and evaluate a new blind benchmark."""

from __future__ import annotations

import importlib.util
import json
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"


def _load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _bootstrap_ci(correct, seed=20261006, samples=5000):
    rng = random.Random(seed)
    n = len(correct)
    vals = []
    for _ in range(samples):
        vals.append(sum(correct[rng.randrange(n)] for _ in range(n)) / n)
    vals.sort()
    lo = vals[int(0.025 * samples)]
    hi = vals[int(0.975 * samples) - 1]
    return {"low": lo, "high": hi, "samples": samples}


def _exact_mcnemar(before_correct, after_correct):
    b = sum(a and not z for a, z in zip(before_correct, after_correct, strict=True))
    c = sum((not a) and z for a, z in zip(before_correct, after_correct, strict=True))
    n = b + c
    if n == 0:
        return {"before_only_correct": b, "after_only_correct": c, "p_value_two_sided": 1.0}
    k = min(b, c)
    prob = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return {
        "before_only_correct": b,
        "after_only_correct": c,
        "p_value_two_sided": min(1.0, 2 * prob),
    }


def run():
    trainer = _load_module(
        STUDY / "experiments" / "run_specialized_crossencoder_sft.py",
        "specialized_sft",
    )
    blind_mod = _load_module(
        STUDY / "experiments" / "generate_task_tool_blind_v1.py",
        "blind_gen",
    )

    blind = blind_mod.generate()
    train_data = json.loads(
        (STUDY / "experiments" / "task_tool_sft_family_split_v1.json").read_text()
    )
    train_rows = [row for row in train_data["rows"] if row["split"] == "train"]
    dev_rows = [row for row in train_data["rows"] if row["split"] == "dev"]
    blind_rows = blind["rows"]

    random.seed(trainer.SEED)
    trainer.np.random.seed(trainer.SEED)
    trainer.torch.manual_seed(trainer.SEED)
    trainer.torch.use_deterministic_algorithms(True)

    tokenizer = trainer.AutoTokenizer.from_pretrained(
        trainer.MODEL_ID, revision=trainer.MODEL_REVISION
    )
    model = trainer.AutoModelForSequenceClassification.from_pretrained(
        trainer.MODEL_ID,
        revision=trainer.MODEL_REVISION,
        num_labels=1,
    )

    before_scores, labels = trainer._predict(model, tokenizer, blind_rows)
    before_metrics = trainer._metrics(before_scores, labels, 0.0)
    before_correct = [
        (score >= 0.0) == bool(label)
        for score, label in zip(before_scores, labels, strict=True)
    ]

    dataset = trainer.PairDataset(train_rows, tokenizer)
    loader = trainer.DataLoader(
        dataset,
        batch_size=trainer.BATCH_SIZE,
        shuffle=True,
        generator=trainer.torch.Generator().manual_seed(trainer.SEED),
        collate_fn=lambda batch: trainer._collate(batch, tokenizer),
    )
    optimizer = trainer.torch.optim.AdamW(model.parameters(), lr=trainer.LEARNING_RATE)
    loss_fn = trainer.torch.nn.BCEWithLogitsLoss()

    model.train()
    for _epoch in range(trainer.EPOCHS):
        for batch in loader:
            y = batch.pop("labels")
            optimizer.zero_grad(set_to_none=True)
            logits = model(**batch).logits.reshape(-1)
            loss = loss_fn(logits, y)
            loss.backward()
            optimizer.step()

    dev_scores, dev_labels = trainer._predict(model, tokenizer, dev_rows)
    threshold, dev_metrics = trainer._threshold(dev_scores, dev_labels)
    after_scores, after_labels = trainer._predict(model, tokenizer, blind_rows)
    after_metrics = trainer._metrics(after_scores, after_labels, threshold)
    after_correct = [
        (score >= threshold) == bool(label)
        for score, label in zip(after_scores, after_labels, strict=True)
    ]

    return {
        "experiment_id": "task-tool-specialized-minilm-blind-v1",
        "blind_dataset_id": blind["dataset_id"],
        "blind_families": blind["families"],
        "blind_count": len(blind_rows),
        "training_recipe": {
            "model_id": trainer.MODEL_ID,
            "model_revision": trainer.MODEL_REVISION,
            "seed": trainer.SEED,
            "epochs": trainer.EPOCHS,
            "batch_size": trainer.BATCH_SIZE,
            "learning_rate": trainer.LEARNING_RATE,
            "train_count": len(train_rows),
            "dev_count": len(dev_rows),
        },
        "before_specialization": before_metrics,
        "after_specialization": after_metrics,
        "calibrated_threshold_from_existing_dev": threshold,
        "dev_metrics": dev_metrics,
        "accuracy_ci_95": _bootstrap_ci(after_correct),
        "paired_mcnemar": _exact_mcnemar(before_correct, after_correct),
        "paper_operational_target": {"accuracy": 0.95, "f1": 0.95},
        "blind_meets_paper_operational_target": (
            after_metrics["accuracy"] >= 0.95 and after_metrics["f1"] >= 0.95
        ),
        "notes": (
            "The blind families were defined and committed before this evaluation. "
            "They were not used for training or threshold selection. This remains an "
            "independent synthetic experiment, not a reproduction of the paper dataset."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
