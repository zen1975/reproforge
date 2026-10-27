"""Independent OPST mechanism primitives (arXiv:2610.32770).

Pure standard-library implementation written from the paper text. No author
code exists or is used. Choices the paper does not specify are marked
"ReproForge choice".
"""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

# ---------------------------------------------------------------------------
# Objective: skewed Jensen-Shannon divergence (paper Sec. 3.5)
# ---------------------------------------------------------------------------


def _check_distribution(p: Sequence[float]) -> None:
    if not p or any(x < 0 for x in p) or abs(sum(p) - 1.0) > 1e-9:
        raise ValueError("expected a non-empty probability vector summing to 1")


def kl(p: Sequence[float], q: Sequence[float]) -> float:
    """KL(p || q) in nats. Terms with p_i == 0 contribute 0."""
    _check_distribution(p)
    _check_distribution(q)
    total = 0.0
    for pi, qi in zip(p, q, strict=True):
        if pi == 0.0:
            continue
        if qi == 0.0:
            return math.inf
        total += pi * math.log(pi / qi)
    return total


def binary_entropy(alpha: float) -> float:
    """H(alpha) in nats."""
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    return -alpha * math.log(alpha) - (1.0 - alpha) * math.log(1.0 - alpha)


def _mix(q: Sequence[float], p: Sequence[float], weight_q: float) -> list[float]:
    return [weight_q * qi + (1.0 - weight_q) * pi for qi, pi in zip(q, p, strict=True)]


def d_alpha_printed(p: Sequence[float], q: Sequence[float], alpha: float) -> float:
    """Divergence exactly as printed in the paper.

    p = student, q = teacher. Mixture q_bar = (1 - alpha) q + alpha p and
    D = alpha KL(q || q_bar) + (1 - alpha) KL(p || q_bar).
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    m = _mix(q, p, 1.0 - alpha)
    return alpha * kl(q, m) + (1.0 - alpha) * kl(p, m)


def d_alpha_consistent(p: Sequence[float], q: Sequence[float], alpha: float) -> float:
    """GKD-consistent form (Agarwal et al., arXiv:2306.13649, Eq. 1).

    Each KL term carries the same weight as its own distribution in the
    mixture: q_bar = alpha q + (1 - alpha) p and
    D = alpha KL(q || q_bar) + (1 - alpha) KL(p || q_bar).
    ReproForge interpretation of the paper's intended objective; see report.
    """
    if not 0.0 < alpha < 1.0:
        raise ValueError("alpha must be in (0, 1)")
    m = _mix(q, p, alpha)
    return alpha * kl(q, m) + (1.0 - alpha) * kl(p, m)


def opst_loss(
    student: Sequence[Sequence[Sequence[float]]],
    teacher: Sequence[Sequence[Sequence[float]]],
    mask: Sequence[Sequence[int]],
    alpha: float,
    divergence=d_alpha_consistent,
) -> float:
    """Paper Eq. (opst_loss): per-sample masked token mean, then batch mean."""
    if not student or len(student) != len(teacher) or len(student) != len(mask):
        raise ValueError("batch shapes must match and be non-empty")
    per_sample = []
    for p_seq, q_seq, m_seq in zip(student, teacher, mask, strict=True):
        if len(p_seq) != len(q_seq) or len(p_seq) != len(m_seq):
            raise ValueError("sequence shapes must match")
        n = sum(m_seq)
        if n == 0:
            raise ValueError("sample has no unmasked tokens")
        per_sample.append(
            sum(m * divergence(p, q, alpha) for p, q, m in zip(p_seq, q_seq, m_seq, strict=True) if m)
            / n
        )
    return sum(per_sample) / len(per_sample)


# ---------------------------------------------------------------------------
# Sample selection: pseudo-verification and consensus gate (paper Sec. 3.4)
# ---------------------------------------------------------------------------


def pseudo_verify(candidate: str, fresh_answer: str, paraphrase_answer: str) -> bool:
    """v(x, z) = I[a_hat(x) = a] * I[a_hat(x') = a]."""
    return fresh_answer == candidate and paraphrase_answer == candidate


def consensus(rollout_answers: Sequence[str], candidate: str) -> float:
    """c(x, z) = (1/G) sum_g I[a_hat_g = a]."""
    if not rollout_answers:
        raise ValueError("consensus gate needs G >= 1 rollouts")
    return sum(a == candidate for a in rollout_answers) / len(rollout_answers)


def normalize_question(text: str) -> str:
    """ReproForge choice: the paper does not specify its duplicate test."""
    return re.sub(r"\s+", " ", text).strip().lower()


def select_samples(samples: Sequence[dict], seen_questions: set[str] | None = None) -> list[dict]:
    """Apply dedupe -> pseudo-verification -> consensus gate.

    Returns one decision per sample: {"id", "keep", "reason", "consensus"}.
    Only c == 1 is discarded by the gate; c == 0 is retained.
    """
    seen = set() if seen_questions is None else seen_questions
    decisions = []
    for s in samples:
        key = normalize_question(s["question"])
        if key in seen:
            decisions.append({"id": s["id"], "keep": False, "reason": "DUPLICATE", "consensus": None})
            continue
        seen.add(key)
        if not pseudo_verify(s["candidate_answer"], s["fresh_answer"], s["paraphrase_answer"]):
            decisions.append({"id": s["id"], "keep": False, "reason": "UNVERIFIED", "consensus": None})
            continue
        c = consensus(s["student_rollouts"], s["candidate_answer"])
        if c == 1.0:
            decisions.append({"id": s["id"], "keep": False, "reason": "TRIVIAL", "consensus": c})
        else:
            decisions.append({"id": s["id"], "keep": True, "reason": "KEPT", "consensus": c})
    return decisions


# ---------------------------------------------------------------------------
# EMA teacher (paper Sec. 3.5, Algorithm 1)
# ---------------------------------------------------------------------------


def ema_update(phi: Sequence[float], theta: Sequence[float], beta: float) -> list[float]:
    """phi_k = (1 - beta) phi_{k-1} + beta theta_k."""
    if not 0.0 < beta <= 1.0:
        raise ValueError("beta must be in (0, 1]")
    return [(1.0 - beta) * f + beta * t for f, t in zip(phi, theta, strict=True)]


def run_rounds(theta0: Sequence[float], student_steps: Sequence[Sequence[Sequence[float]]], beta: float) -> dict:
    """Run Algorithm 1's weight bookkeeping.

    student_steps[n][k] is the student weight vector after gradient step k of
    round n. The teacher is updated after every gradient step and both carry
    over between rounds. Returns the EMA teacher (the evaluated model).
    """
    theta = list(theta0)
    phi = list(theta0)
    updates = 0
    for round_steps in student_steps:
        for theta_k in round_steps:
            theta = list(theta_k)
            phi = ema_update(phi, theta, beta)
            updates += 1
    return {"returned": phi, "student": theta, "ema_updates": updates}
