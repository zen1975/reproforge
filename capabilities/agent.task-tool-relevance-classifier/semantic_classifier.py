"""Optional model-backed runtime for task-tool relevance classification.

The shipped default capability remains the deterministic lexical reference.
This module loads an independently trained local sequence-classification checkpoint.
"""

from __future__ import annotations

import json
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer


class SemanticTaskToolClassifier:
    def __init__(self, model_dir: str | Path, threshold: float | None = None):
        self.model_dir = Path(model_dir)
        metadata_path = self.model_dir / "reproforge_metadata.json"
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        self.threshold = float(
            metadata.get("threshold", 0.0) if threshold is None else threshold
        )
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_dir, local_files_only=True)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_dir,
            local_files_only=True,
        )
        self.model.eval()

    def classify(self, task: str, tool_name: str, tool_description: str) -> dict:
        if not task.strip() or not tool_name.strip() or not tool_description.strip():
            raise ValueError("task, tool_name, and tool_description must be non-empty")
        encoded = self.tokenizer(
            task,
            f"{tool_name}: {tool_description}",
            truncation=True,
            max_length=96,
            return_tensors="pt",
        )
        with torch.no_grad():
            score = float(self.model(**encoded).logits.reshape(-1)[0].item())
        return {
            "relevance_score": score,
            "relevant": score >= self.threshold,
            "method": "specialized-crossencoder-local-v1",
            "threshold": self.threshold,
        }
