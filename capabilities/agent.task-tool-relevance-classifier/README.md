# Task-Tool Relevance Classifier

Status: `experimental`  
Paper reproduction status: `PARTIAL`

This capability represents the provider-neutral system idea extracted from arXiv:2610.03213: evaluate each candidate tool independently against the assigned task and emit a relevance signal before execution.

The included Python implementation is a deterministic lexical reference baseline only. It is intentionally not described as the paper's SLM method and does not reproduce the reported GEPA, SFT, or GRPO experiments.

## Independent hard synthetic benchmark

ReproForge now includes a 32-case candidate-level benchmark with positive, wrong-tool, paraphrase, and lexical-overlap hard-negative examples.

Measured result for `lexical-overlap-reference-v1`:

- accuracy: 50.0%
- precision: 47.83%
- recall: 73.33%
- F1: 57.89%
- false-positive rate: 70.59%
- false-negative rate: 26.67%

The paper defines an operational target of 95% accuracy and 95% F1. The lexical baseline fails that target by a wide margin. That is useful evidence: keyword overlap is not sufficient for intent-aware tool-call oversight.

This benchmark is independent synthetic mechanism evidence, not the paper's held-out server-disjoint dataset.

## Off-the-shelf semantic baseline

ReproForge also ran `cross-encoder/ms-marco-MiniLM-L6-v2` (Apache-2.0) on the same benchmark. With the model's raw score threshold fixed at 0.0, accuracy was 56.25% and F1 was 30.0%.

To avoid tuning on the whole set, the first 16 cases were then used only to calibrate a scalar threshold, and the remaining 16 cases were held out for test scoring. The calibrated test result was:

- accuracy: 37.5%
- precision: 36.36%
- recall: 57.14%
- F1: 44.44%
- false-positive rate: 77.78%
- false-negative rate: 42.86%

So a generic semantic relevance model did **not** solve task-tool intent matching and did not outperform the lexical reference on this independent test split. This strengthens the case for task-specific supervision or instruction tuning rather than generic semantic similarity alone.

The paper's Gemma 3 Base → GEPA → SFT → GRPO results remain unreproduced.

## Task-specific supervised specialization

A third experiment fine-tunes the pinned MiniLM CrossEncoder on a deterministic synthetic dataset with tool-family-disjoint splits:

- train: 288 examples across 8 families;
- dev: 72 examples across 2 unseen families;
- test: 72 examples across 2 additional unseen families;
- 3 epochs, batch size 16, learning rate 2e-5;
- test families were frozen as `translate` and `database`.

The same base model scored 80.56% accuracy / 69.57% F1 on that held-out test before specialization. After supervised task-specific fine-tuning:

- accuracy: 91.67%
- precision: 100%
- recall: 75%
- F1: 85.71%
- false-positive rate: 0%
- false-negative rate: 25%

That is +11.11 percentage points in accuracy and +16.15 points in F1. The result is still below the paper's 95% accuracy/F1 operational target, so the capability remains experimental and the paper reproduction remains PARTIAL.

This trained checkpoint is an experiment artifact, not the shipped runtime implementation. The production descriptor still points to the transparent lexical reference until a model-backed runtime is independently validated and packaged.

## Frozen blind generalization check

After the first held-out result had already been observed, ReproForge defined a **new** blind benchmark before evaluation. It contains 144 examples from four entirely new families: `commerce`, `documents`, `identity`, and `notifications`. None of those families participate in training or threshold selection.

Using the same frozen training recipe, the base model scored 85.42% accuracy / 78.79% F1. After task-specific specialization:

- accuracy: 94.44%
- precision: 95.45%
- recall: 87.50%
- F1: 91.30%
- false-positive rate: 2.08%
- false-negative rate: 12.50%

The paired comparison had 13 cases corrected by specialization and 0 cases made worse; exact McNemar p = 0.000244. A 5,000-sample bootstrap placed accuracy at 90.28%–97.92% (95% interval).

This is stronger evidence that specialization generalizes beyond the originally observed test families. It still does **not** satisfy the paper's joint 95% accuracy/F1 target, because observed accuracy is 94.44% and F1 is 91.30%.

## Model-backed runtime path

ReproForge now also includes an optional local checkpoint runtime in `semantic_classifier.py`. The export workflow independently trains the specialized model, writes tokenizer/model files plus `reproforge_metadata.json`, reloads them using `local_files_only=True`, and exercises the stable `classify(task, tool_name, tool_description)` contract.

The export/reload smoke test passed 4/4 positive and wrong-action examples. The resulting checkpoint was about 83.4 MB and is kept only as a one-day GitHub Actions artifact; the durable repository stores the training recipe, model revision, model SHA256, calibrated threshold, and Evidence instead of committing weights.

This makes the specialized classifier reproducibly callable without promoting it to the default runtime yet. The default descriptor intentionally remains the deterministic lexical implementation until a model-backed package has stronger protocol-equivalent evidence.

## Protocol-equivalent SLM chain

ReproForge now also has an independent structural reproduction of the paper's evaluation shape: 12 synthetic MCP-style servers, an 8/4 server-disjoint split, N=2/3 multi-tool tasks, and candidate-level `correct / wrong / null` classification.

Using the ungated Apache-2.0 `Qwen/Qwen2.5-0.5B-Instruct` strictly as a model-class proxy:

| Stage | Accuracy | F1 | Parse failures |
| --- | ---: | ---: | ---: |
| Initial Base prompt | 31.25% | 47.62% | 64 / 160 |
| Prompt-optimization analogue | 80.00% | 76.12% | 0 / 160 |
| LoRA SFT analogue v1 | 95.00% | 92.86% | 0 / 80 |

The prompt stage selected one of three fixed prompt candidates using only train-pool dev rows; it is **not GEPA**. The LoRA stage fine-tuned only 270,336 parameters (r=4, alpha=8, q_proj/v_proj) on 96 train-pool rows and evaluated a frozen held-out-server slice.

SFT v1 reached the paper's 95% accuracy threshold but not the 95% F1 threshold. Therefore the joint operational target is still not met. These are protocol-equivalent proxy experiments, not Gemma 3 or author-dataset reproduction.

### Frozen SFT v2 check

To test whether simply adding more synthetic supervision would close the gap, ReproForge predeclared SFT v2 before evaluation. It kept the model revision, prompt, LoRA r/alpha/modules, learning rate, and seed fixed; only training rows increased from 96 to 192. Evaluation moved to a previously untouched 240-row held-out slice (rows 160–399).

Result:

- accuracy: 90.83%
- precision: 79.00%
- recall: 98.75%
- F1: 87.78%
- false positives: 21
- false negatives: 1

So more synthetic training data alone **reduced** held-out performance. The new slice is frozen and will not be tuned against. This is useful negative evidence: the remaining gap is not solved by naively scaling the same synthetic recipe.

## Contract

Input:
- `task`
- `tool_name`
- `tool_description`

Output:
- `relevance_score`
- `relevant`
- `method`

## Promotion gate

Promotion to `verified` requires a semantic-model implementation, protocol-equivalent server-disjoint data, comparison against the paper's accuracy/F1/E2E metrics, and preserved machine-checkable evidence.
