"""Selector arms for jev-live-systemone-check-v2: Jev, and the named LLM candidate-interface control.

Both expose choose(state, instructions, criteria, oracle=None) -> decision dict (v1 shape), see
jev_v2_core.py. The control is NEVER presented as Jev: it is "LLM candidate-interface control
(claude-haiku-5-5)". Facts pinned from current Anthropic docs (2026-10-14, claude-api skill):
claude-haiku-5-5 rejects non-default sampling parameters (temperature must be 1, top_p 0.99; both are
omitted here, so the control is stochastic), accepts a forced tool_choice (then skips thinking), and
is priced at $0.10 / $0.50 per MTok for prompts <= 100K tokens.
"""
from __future__ import annotations

import time

import jev_v2_core as core  # noqa: F401  (registers v1 helpers via core.v1)

v1 = core.v1

CONTROL_MODEL = "claude-haiku-5-5"
CONTROL_PRICING = {"usd_per_million_input_tokens": 0.10, "usd_per_million_output_tokens": 0.50}
CONTROL_SYSTEM = (
    "You are the action selector in a software workflow. You always answer by calling the "
    "select_action tool exactly once with one of the listed candidates."
)
TOOL_NAME = "select_action"
RETRY_BACKOFF = (1, 2, 4, 8, 16)


class SpendCapReached(RuntimeError):
    pass


class SpendGuard:
    """Runner-enforced spend cap shared by all calls of one arm process."""

    def __init__(self, cap_usd: float, pricing: dict):
        self.cap, self.pricing, self.spent = cap_usd, pricing, 0.0

    def charge(self, usage: dict) -> None:
        self.spent += v1.cost_usd(usage, self.pricing)
        if self.spent > self.cap:
            raise SpendCapReached(f"spend cap ${self.cap:.2f} exceeded (${self.spent:.4f})")


def render_candidates(criteria: dict) -> str:
    """Candidates in exactly the order Jev receives (position is a measured factor)."""
    return "\n".join(f"- {name}: {desc}" for name, desc in criteria.items())


def build_control_request(state: str, instructions: str, criteria: dict, model: str = CONTROL_MODEL) -> dict:
    return {
        "model": model,
        "max_tokens": 256,
        "system": CONTROL_SYSTEM,
        "output_config": {"effort": "low"},
        "tools": [{
            "name": TOOL_NAME,
            "description": "Select the single best next action.",
            "strict": True,
            "input_schema": {
                "type": "object",
                "properties": {"choice": {"type": "string", "enum": list(criteria)}},
                "required": ["choice"],
                "additionalProperties": False,
            },
        }],
        "tool_choice": {"type": "tool", "name": TOOL_NAME},
        "messages": [{
            "role": "user",
            "content": f"{state}\n\n{instructions}\n\nCandidates (in this order):\n{render_candidates(criteria)}",
        }],
    }


def _retryable(exc: Exception) -> bool:
    status = getattr(exc, "status_code", None)
    if status is not None:
        return status in (429, 529) or status >= 500
    return type(exc).__name__ in ("APIConnectionError", "APITimeoutError")


class ControlArm:
    """LLM candidate-interface control via the official Anthropic SDK (client injected for tests).

    SDK retries must be disabled (max_retries=0) so backoff is logged separately from latency."""

    def __init__(self, client, guard: SpendGuard | None = None, model: str = CONTROL_MODEL, sleep=time.sleep):
        self.client, self.guard, self.model, self._sleep = client, guard, model, sleep

    def choose(self, state: str, instructions: str, criteria: dict, oracle=None):
        req = build_control_request(state, instructions, criteria, self.model)
        retries, waited = 0, 0.0
        while True:
            t0 = time.perf_counter()
            try:
                resp = self.client.messages.create(**req)
                latency = time.perf_counter() - t0
                break
            except Exception as exc:  # noqa: BLE001 - classified below, never swallowed silently
                if _retryable(exc) and retries < len(RETRY_BACKOFF):
                    self._sleep(RETRY_BACKOFF[retries])
                    waited += RETRY_BACKOFF[retries]
                    retries += 1
                    continue
                return v1.make_decision(None, valid=False, infra=True, retries=retries, retry_wait_s=waited,
                                        error=f"{type(exc).__name__}:{getattr(exc, 'status_code', '')}"[:200])
        usage = {"input_tokens": getattr(resp.usage, "input_tokens", 0),
                 "output_tokens": getattr(resp.usage, "output_tokens", 0)}
        if self.guard:
            self.guard.charge(usage)
        choice = None
        for block in resp.content:
            if getattr(block, "type", None) == "tool_use" and block.name == TOOL_NAME:
                choice = (block.input or {}).get("choice")
        valid = choice in criteria
        d = v1.make_decision(
            choice if valid else None, valid=valid, latency_s=latency, usage=usage,
            model=getattr(resp, "model", None), retries=retries, retry_wait_s=waited,
            error=None if valid else "unparseable_or_out_of_set_choice",
        )
        d["stop_reason"] = getattr(resp, "stop_reason", None)
        d["request_id"] = getattr(resp, "_request_id", None)
        return d


class JevArm:
    """Jev via the frozen v1 client (Choice question), guarded by the same spend cap mechanism."""

    def __init__(self, client, model: str = "jev-1.13.0", guard: SpendGuard | None = None):
        self.live, self.guard = v1.LiveSelector(client, model), guard

    def choose(self, state: str, instructions: str, criteria: dict, oracle=None):
        d = self.live.choose(state, instructions, criteria)
        if self.guard:
            self.guard.charge(d["usage"])
        return d
