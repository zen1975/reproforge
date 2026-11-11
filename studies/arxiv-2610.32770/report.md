# Study report — arXiv:2610.32770 (OPST), 2026-10-27

Run `opst-mechanism-v1` (standard library only). The acceptance criteria and the C1 hypothesis (printed form fails) were fixed in the pre-registration commit `b6035ac`; the unit tests had been executed once in the working tree before that commit, and no criterion, probe or fixture changed afterwards. All four mechanism claims PASS. Paper-level claim C5 is not tested.

## C1 — objective semantics (finding)

Sec. 3.5 prints the mixture as `q_bar = (1-alpha) q + alpha p` with `D = alpha KL(q||q_bar) + (1-alpha) KL(p||q_bar)`, and states that D recovers forward KL as alpha->0, reverse KL as alpha->1, and is bounded by H(alpha).

On p=[0.7,0.2,0.1], q=[0.1,0.3,0.6] (KL(q||p)=1.0021, KL(p||q)=1.1019):

| Form | D/alpha -> KL(q‖p) as alpha->0 | D/(1-alpha) -> KL(p‖q) as alpha->1 | D <= H(alpha) | D at alpha=0.8 |
|---|---|---|---|---|
| Printed | no (error grows 1.38 -> 1.1e4) | no (1.25 -> 1.0e4) | 10/14 violations | 0.4698 |
| GKD-consistent `q_bar = alpha q + (1-alpha) p` | yes (0.253 -> 1.5e-4) | yes (0.315 -> 2.0e-4) | 0 violations | 0.1574 |

With the printed weighting the limits are swapped: D itself tends to KL(p‖q) as alpha->0 (D=1.097 at alpha=0.001 vs 1.1019) and to KL(q‖p) as alpha->1 (D=0.998 at alpha=0.999 vs 1.0021), so alpha=0.8 would lean towards forward KL, which also contradicts the stated "favors the mode-seeking regime". The GKD-consistent weighting (each KL weighted like its own distribution in the mixture, Agarwal et al. arXiv:2306.13649 Eq. 1, which the paper cites as its basis) satisfies all stated properties. Most likely a typesetting slip in the mixture; which form the authors' code used is unknown. ReproForge analogues use the consistent form, labeled as an interpretation.

## C2 — sample selection

12/12 frozen cases match (5 kept). Boundary results preserved:

- the consensus gate retains c=0 samples: it never rejects disagreement, only full agreement;
- a wrong candidate answer that the generator reproduces consistently (fresh and paraphrased) passes both filters (`s06`). Pseudo-verification checks stability, not correctness. Robustness to such samples rests on the objective (teacher conditioned on, not imitating, z), which is claim C5 territory.

## C3 / C4 — EMA teacher and loss aggregation

EMA updates once per gradient step (10 over 2x5 steps), carries across rounds, matches the closed form within 1e-12; beta=1 returns the student; the returned model is the teacher. The loss is padding-invariant and averages per sample before the batch (d/2, not the token-pooled d/5).

## Not established

No self-improvement, SFT comparison or benchmark number from the paper is reproduced, and the wrong-answer robustness analogue (C6) is INCONCLUSIVE. reproduction_status remains PARTIAL.

## C6 — wrong-answer robustness analogue (2026-11-12): INCONCLUSIVE

Frozen `opst-wrong-answer-robustness-qwen0.5b-v1`, pre-registered in `fc59acd` (`experiments/opst_wr_preregistration_v1.json`) and dispatched once as GitHub Actions run 43065895170 (12 cells + aggregate, all jobs succeeded). Qwen2.5-0.5B-Instruct (pinned `c89bee90…`), LoRA, one round of 32 steps on 64 synthetic arithmetic questions per seed, p ∈ {0, 0.75}, 3 seeds. Every value the paper does not publish is a ReproForge choice listed in `experiments/opst_wr_config_v1.json`. The aggregate re-computed from the downloaded cells is identical to the CI aggregate.

Held-out (200 questions, never scored before this run), mean over 3 seeds; base model accuracy 0.415, mean gold log-prob −1.242:

| Cell | Mean gold log-prob | Accuracy |
|---|---|---|
| SFT, p=0 | −1.275 | 0.455 |
| SFT, p=0.75 | −1.263 | 0.413 |
| OPST (EMA teacher), p=0 | −1.261 | 0.410 |
| OPST (EMA teacher), p=0.75 | −1.282 | 0.418 |

Drop p=0→0.75: SFT −0.013 nats (per seed −0.014, −0.049, +0.024), OPST +0.021 nats (−0.007, +0.063, +0.006). OPST dropped less in 1 of 3 seeds.

Guards (any failure ⇒ INCONCLUSIVE):

| Guard | Result |
|---|---|
| Base accuracy in [0.30, 0.90] | holds (0.415) |
| SFT degraded by corruption (mean drop ≥ 0.02) | **fails** (−0.013) |
| OPST moved on its training questions (≥ 0.02) | **fails** (0.006) |
| Base evaluation identical across cells (6 decimals) | **fails**: values differ by ~5e-7 across runners (float32 CPU nondeterminism). The pre-registered tolerance was too strict; this alone would not have changed the outcome because the two guards above also fail. |

Verdict: **INCONCLUSIVE**. The corruption did not measurably hurt SFT, so this run cannot say whether OPST is more robust. No conclusion in either direction is drawn.

Post-hoc observations (not part of the verdict, recorded to inform a new version):

- SFT memorised z (train loss → 0.000 at p=0, 0.08 at p=0.75), yet the held-out letter metric barely moved and even the training questions' gold metric fell (−0.01 to −0.18). Training used the `Solution:` prompt and target format, while evaluation scores a letter after `Answer:`; the learned behaviour appears not to transfer to the evaluation format.
- OPST's per-token divergence was small from the start (0.01–0.04) and the EMA teacher (β=0.05, 32 updates) moved little. One seed (202) at p=0.75 lowered the training questions' gold metric by 0.12, which suggests the teacher conditioned on a wrong z can pass it on, but one seed is not evidence.
- Sampled rollouts are often off-format prose at temperature 1.0.

A follow-up must use a new evaluation id and new held-out questions (for example, evaluating in the training format, more steps, or a manipulation check calibrated on a separate split before registration).
