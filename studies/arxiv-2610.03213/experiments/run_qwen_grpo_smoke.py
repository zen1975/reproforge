"""Minimal real GRPO smoke test for task-tool relevance.

Purpose: verify that ReproForge can execute a genuine GRPOTrainer update path
with a task-specific reward. This is NOT a paper benchmark and NOT the paper's
Gemma/SFT->GRPO reproduction.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from datasets import Dataset
from peft import LoraConfig
from trl import GRPOConfig, GRPOTrainer

ROOT=Path(__file__).resolve().parents[3]
STUDY=ROOT/"studies"/"arxiv-2610.03213"
MODEL_ID="Qwen/Qwen2.5-0.5B-Instruct"
MODEL_REVISION="c89bee90d9f811437d9735454613c35b4a3c4dc8"

SYSTEM=(
    "You are a strict task-tool relevance classifier. "
    "The action and object must match. Output exactly TRUE or FALSE."
)


def _prompt(row):
    return (
        f"{SYSTEM}\n"
        f"TASK: {row['task']}\n"
        f"CANDIDATE TOOL: {row['tool_name']}\n"
        f"DESCRIPTION: {row['tool_description']}\n"
        "ANSWER:"
    )


def reward_func(completions, label, **kwargs):
    rewards=[]
    for completion, expected in zip(completions,label,strict=True):
        if isinstance(completion,list):
            text=completion[-1].get("content","") if completion else ""
        else:
            text=str(completion)
        m=re.search(r"\b(TRUE|FALSE)\b",text.upper())
        if not m:
            rewards.append(-0.5)
            continue
        pred=1 if m.group(1)=="TRUE" else 0
        rewards.append(1.0 if pred==int(expected) else -1.0)
    return rewards


def run():
    data=json.loads((STUDY/"experiments"/"protocol_equivalent_mcp_v1.json").read_text())
    rows=[r for r in data["rows"] if r["pool"]=="train"][:8]
    ds=Dataset.from_list([
        {"prompt":_prompt(row),"label":int(row["label"])}
        for row in rows
    ])
    args=GRPOConfig(
        output_dir="/tmp/reproforge-grpo-smoke",
        model_init_kwargs={"revision":MODEL_REVISION,"dtype":"float32"},
        use_cpu=True,
        per_device_train_batch_size=2,
        gradient_accumulation_steps=1,
        num_generations=2,
        max_completion_length=4,
        max_steps=2,
        learning_rate=1e-5,
        logging_steps=1,
        save_strategy="no",
        report_to="none",
        remove_unused_columns=False,
        use_vllm=False,
        seed=20261006,
    )
    trainer=GRPOTrainer(
        model=MODEL_ID,
        args=args,
        reward_funcs=reward_func,
        train_dataset=ds,
        peft_config=LoraConfig(
            r=2,
            lora_alpha=4,
            lora_dropout=0.0,
            bias="none",
            task_type="CAUSAL_LM",
            target_modules=["q_proj","v_proj"],
        ),
    )
    result=trainer.train()
    metrics={k:(float(v) if isinstance(v,(int,float)) else v) for k,v in result.metrics.items()}
    return {
        "experiment_id":"qwen2.5-0.5b-grpo-smoke-v1",
        "model_id":MODEL_ID,
        "model_revision":MODEL_REVISION,
        "train_rows":len(rows),
        "max_steps":2,
        "num_generations":2,
        "reward":"exact TRUE/FALSE correctness: +1 correct, -1 wrong, -0.5 unparseable",
        "trainer_metrics":metrics,
        "completed":True,
        "boundary":"Real GRPOTrainer smoke only; not a performance benchmark or paper GRPO reproduction.",
    }


if __name__=="__main__":
    print(json.dumps(run(),indent=2,sort_keys=True))
