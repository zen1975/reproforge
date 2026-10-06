"""Train, export, reload, and smoke-test the specialized classifier."""

from __future__ import annotations

import importlib.util
import json
import random
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT / "studies" / "arxiv-2610.03213"
CAPABILITY = ROOT / "capabilities" / "agent.task-tool-relevance-classifier"
EXPORT = ROOT / "artifacts" / "task-tool-specialized-minilm-v1"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run():
    trainer = _load(
        STUDY / "experiments" / "run_specialized_crossencoder_sft.py",
        "specialized_sft_export",
    )
    runtime = _load(CAPABILITY / "semantic_classifier.py", "semantic_runtime")
    data = json.loads(
        (STUDY / "experiments" / "task_tool_sft_family_split_v1.json").read_text()
    )
    train_rows = [row for row in data["rows"] if row["split"] == "train"]
    dev_rows = [row for row in data["rows"] if row["split"] == "dev"]

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
            labels = batch.pop("labels")
            optimizer.zero_grad(set_to_none=True)
            logits = model(**batch).logits.reshape(-1)
            loss = loss_fn(logits, labels)
            loss.backward()
            optimizer.step()

    dev_scores, dev_labels = trainer._predict(model, tokenizer, dev_rows)
    threshold, dev_metrics = trainer._threshold(dev_scores, dev_labels)
    model_sha = trainer._model_hash(model)

    if EXPORT.exists():
        shutil.rmtree(EXPORT)
    EXPORT.mkdir(parents=True)
    tokenizer.save_pretrained(EXPORT)
    model.save_pretrained(EXPORT, safe_serialization=True)
    (EXPORT / "reproforge_metadata.json").write_text(
        json.dumps(
            {
                "threshold": threshold,
                "model_sha256": model_sha,
                "base_model_id": trainer.MODEL_ID,
                "base_model_revision": trainer.MODEL_REVISION,
                "seed": trainer.SEED,
                "training_recipe": "task-tool-specialized-minilm-sft-v1",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )

    loaded = runtime.SemanticTaskToolClassifier(EXPORT)
    smoke = [
        (
            "create a calendar event",
            "calendar_create_event",
            "create a calendar event with date time and attendees",
            True,
        ),
        (
            "create a calendar event",
            "calendar_delete_event",
            "delete an existing calendar event",
            False,
        ),
        (
            "send an email message",
            "email_send",
            "send an email message to recipients",
            True,
        ),
        (
            "send an email message",
            "email_delete",
            "delete an email message",
            False,
        ),
    ]
    results = []
    for task, name, description, expected in smoke:
        prediction = loaded.classify(task, name, description)
        results.append({"expected": expected, **prediction})
    if not all(item["expected"] == item["relevant"] for item in results):
        raise RuntimeError(f"reload smoke test failed: {results}")

    return {
        "export_path": str(EXPORT),
        "model_sha256": model_sha,
        "threshold": threshold,
        "dev_metrics": dev_metrics,
        "smoke_count": len(results),
        "smoke_passed": True,
        "results": results,
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
