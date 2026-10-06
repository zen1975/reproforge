"""Task-specific supervised fine-tuning experiment for task-tool relevance."""

from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

import numpy as np
import torch
from torch.utils.data import DataLoader, Dataset
from transformers import AutoModelForSequenceClassification, AutoTokenizer

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
DATA_PATH = STUDY / "experiments" / "task_tool_sft_family_split_v1.json"
MODEL_ID = "cross-encoder/ms-marco-MiniLM-L6-v2"
MODEL_REVISION = "ce0834f22110de6d9222af7a7a03628121708969"
SEED = 20261006
EPOCHS = 3
BATCH_SIZE = 16
LEARNING_RATE = 2e-5
MAX_LENGTH = 96


class PairDataset(Dataset):
    def __init__(self, rows, tokenizer):
        self.rows = rows
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, idx):
        row = self.rows[idx]
        encoded = self.tokenizer(
            row["task"],
            f'{row["tool_name"]}: {row["tool_description"]}',
            truncation=True,
            max_length=MAX_LENGTH,
            padding=False,
        )
        encoded["labels"] = float(row["label"])
        return encoded


def _collate(batch, tokenizer):
    labels = torch.tensor([item.pop("labels") for item in batch], dtype=torch.float32)
    padded = tokenizer.pad(batch, padding=True, return_tensors="pt")
    padded["labels"] = labels
    return padded


def _metrics(scores, labels, threshold):
    preds = [score >= threshold for score in scores]
    tp = sum(pred and label == 1 for pred, label in zip(preds, labels, strict=True))
    tn = sum((not pred) and label == 0 for pred, label in zip(preds, labels, strict=True))
    fp = sum(pred and label == 0 for pred, label in zip(preds, labels, strict=True))
    fn = sum((not pred) and label == 1 for pred, label in zip(preds, labels, strict=True))
    n = len(labels)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {
        "accuracy": (tp + tn) / n,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fp / (fp + tn) if fp + tn else 0.0,
        "false_negative_rate": fn / (fn + tp) if fn + tp else 0.0,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def _threshold(dev_scores, dev_labels):
    values = sorted(set(dev_scores))
    candidates = [values[0] - 1.0, values[-1] + 1.0]
    candidates.extend(values)
    candidates.extend((a + b) / 2 for a, b in zip(values, values[1:], strict=False))
    best = None
    for threshold in candidates:
        metrics = _metrics(dev_scores, dev_labels, threshold)
        key = (metrics["f1"], metrics["accuracy"], -abs(threshold))
        if best is None or key > best[0]:
            best = (key, threshold, metrics)
    assert best is not None
    return best[1], best[2]


def _predict(model, tokenizer, rows):
    model.eval()
    scores = []
    labels = []
    with torch.no_grad():
        for row in rows:
            batch = tokenizer(
                row["task"],
                f'{row["tool_name"]}: {row["tool_description"]}',
                truncation=True,
                max_length=MAX_LENGTH,
                return_tensors="pt",
            )
            score = model(**batch).logits.reshape(-1)[0].item()
            scores.append(float(score))
            labels.append(int(row["label"]))
    return scores, labels


def _model_hash(model):
    h = hashlib.sha256()
    for name, tensor in sorted(model.state_dict().items()):
        h.update(name.encode())
        h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def run():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)
    torch.use_deterministic_algorithms(True)

    data = json.loads(DATA_PATH.read_text())
    rows = data["rows"]
    train_rows = [row for row in rows if row["split"] == "train"]
    dev_rows = [row for row in rows if row["split"] == "dev"]
    test_rows = [row for row in rows if row["split"] == "test"]

    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, revision=MODEL_REVISION)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_ID,
        revision=MODEL_REVISION,
        num_labels=1,
    )

    initial_test_scores, initial_test_labels = _predict(model, tokenizer, test_rows)
    initial_test_metrics = _metrics(initial_test_scores, initial_test_labels, 0.0)

    dataset = PairDataset(train_rows, tokenizer)
    loader = DataLoader(
        dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
        generator=torch.Generator().manual_seed(SEED),
        collate_fn=lambda batch: _collate(batch, tokenizer),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=LEARNING_RATE)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    model.train()
    losses = []
    for _epoch in range(EPOCHS):
        for batch in loader:
            labels = batch.pop("labels")
            optimizer.zero_grad(set_to_none=True)
            logits = model(**batch).logits.reshape(-1)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))

    dev_scores, dev_labels = _predict(model, tokenizer, dev_rows)
    threshold, dev_metrics = _threshold(dev_scores, dev_labels)
    test_scores, test_labels = _predict(model, tokenizer, test_rows)
    test_metrics = _metrics(test_scores, test_labels, threshold)

    return {
        "experiment_id": "task-tool-specialized-minilm-sft-v1",
        "dataset_id": data["dataset_id"],
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "seed": SEED,
        "epochs": EPOCHS,
        "batch_size": BATCH_SIZE,
        "learning_rate": LEARNING_RATE,
        "max_length": MAX_LENGTH,
        "counts": {
            "train": len(train_rows),
            "dev": len(dev_rows),
            "test": len(test_rows),
        },
        "families": data["splits"],
        "initial_untrained_test_at_threshold_0": initial_test_metrics,
        "training": {
            "steps": len(losses),
            "first_loss": losses[0],
            "last_loss": losses[-1],
            "mean_loss": sum(losses) / len(losses),
        },
        "calibrated_threshold": threshold,
        "dev_metrics": dev_metrics,
        "test_metrics": test_metrics,
        "paper_operational_target": {"accuracy": 0.95, "f1": 0.95},
        "test_meets_paper_operational_target": (
            test_metrics["accuracy"] >= 0.95 and test_metrics["f1"] >= 0.95
        ),
        "trained_model_sha256": _model_hash(model),
        "notes": (
            "Independent supervised fine-tuning analogue on deterministic synthetic data. "
            "Tool families are disjoint across train/dev/test. This is not the paper dataset "
            "and does not reproduce Gemma 3, GEPA, SFT, or GRPO settings."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
