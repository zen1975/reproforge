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

No self-improvement, SFT comparison, wrong-answer robustness or benchmark number from the paper is reproduced. reproduction_status remains PARTIAL.
