"""Auxiliary stage for jev-live-systemone-check-v3b (design: ../design/jev-live-systemone-check-v3b.md).

A T3A-style auxiliary-generation analogue ("LLM auxiliary generator (claude-haiku-5-5)"): before every ACTION
decision (never before completion verification) one haiku call sees only the rendered state and writes a short
note that is appended to the state the selector receives. Identical in kind for B, C and J. The auxiliary call
never sees the oracle and is told not to recommend an action. Its latency/tokens/cost are accounted separately
from the selector's decision latency/tokens/cost.
"""
from __future__ import annotations

import time

import jev_v2_arms as v2arms
import jev_v2_core as core

v1 = core.v1
AUX_MODEL = v2arms.CONTROL_MODEL
AUX_PRICING = v2arms.CONTROL_PRICING
AUX_MAX_TOKENS = 150
AUX_SYSTEM = (
    "You write short factual notes about the current state of a software workflow. You never recommend or "
    "choose an action."
)
AUX_INSTRUCTION = (
    "Write a note of at most three sentences: which conditions of the goal appear already met or unmet, and "
    "which prerequisites matter for the next step. Do not recommend or choose an action."
)
NOTE_HEADER = "Assistant note about the state:"


def build_aux_request(state: str, model: str = AUX_MODEL) -> dict:
    return {
        "model": model, "max_tokens": AUX_MAX_TOKENS, "system": AUX_SYSTEM,
        "output_config": {"effort": "low"},
        "messages": [{"role": "user", "content": f"{state}\n\n{AUX_INSTRUCTION}"}],
    }


def is_verification(criteria: dict) -> bool:
    return set(criteria) == set(core.VERIFICATION_CRITERIA)


def zero_aux() -> dict:
    return {"aux_calls": 0, "aux_latency_total_s": 0.0, "aux_usage": {"input_tokens": 0, "output_tokens": 0},
            "aux_cost_usd": 0.0}


class AuxWrapped:
    """Wraps any v2/v3 selector. `drain()` returns (and resets) the auxiliary accounting for one episode."""

    def __init__(self, selector, aux_client, guard=None, model: str = AUX_MODEL, sleep=time.sleep):
        self.selector, self.client, self.guard, self.model, self._sleep = selector, aux_client, guard, model, sleep
        self._acc = zero_aux()

    def drain(self) -> dict:
        out, self._acc = self._acc, zero_aux()
        return out

    def _note(self, state: str):
        req = build_aux_request(state, self.model)
        retries = 0
        while True:
            t0 = time.perf_counter()
            try:
                resp = self.client.messages.create(**req)
                latency = time.perf_counter() - t0
                break
            except Exception as exc:  # noqa: BLE001 - becomes an infrastructure failure, never swallowed
                if v2arms._retryable(exc) and retries < len(v2arms.RETRY_BACKOFF):
                    self._sleep(v2arms.RETRY_BACKOFF[retries])
                    retries += 1
                    continue
                return None, f"{type(exc).__name__}:{getattr(exc, 'status_code', '')}"[:200]
        usage = {"input_tokens": getattr(resp.usage, "input_tokens", 0),
                 "output_tokens": getattr(resp.usage, "output_tokens", 0)}
        if self.guard:
            self.guard.charge(usage)
        a = self._acc
        a["aux_calls"] += 1
        a["aux_latency_total_s"] += latency
        a["aux_usage"]["input_tokens"] += usage["input_tokens"]
        a["aux_usage"]["output_tokens"] += usage["output_tokens"]
        a["aux_cost_usd"] += v1.cost_usd(usage, AUX_PRICING)
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", None) == "text").strip()
        return text, None

    def choose(self, state: str, instructions: str, criteria: dict, oracle=None):
        if is_verification(criteria):
            return self.selector.choose(state, instructions, criteria, oracle)
        note, err = self._note(state)
        if err is not None:
            return v1.make_decision(None, valid=False, infra=True, error=f"aux_failure:{err}")
        return self.selector.choose(f"{state}\n\n{NOTE_HEADER}\n{note}", instructions, criteria, oracle)
