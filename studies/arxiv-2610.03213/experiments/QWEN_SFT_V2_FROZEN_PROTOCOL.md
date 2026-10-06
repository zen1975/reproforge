# Frozen Evaluation Protocol — Qwen LoRA SFT v2

Declared before evaluation.

- Base model: `Qwen/Qwen2.5-0.5B-Instruct`
- Revision: `c89bee90d9f811437d9735454613c35b4a3c4dc8`
- LoRA: r=4, alpha=8, q_proj/v_proj
- LR: 2e-4
- Seed: 20261006
- Prompt/system instruction: unchanged from SFT v1
- Only intentional training change: 96 → 192 train-pool candidate rows
- Evaluation: held-out server-pool rows `[160:400]` (240 rows)
- These rows were not used by Base v1, Prompt v1, or SFT v1 evaluation.
- Joint pass criterion: Accuracy >= 0.95 AND F1 >= 0.95.
- No parameter adjustment is allowed after observing this slice.
