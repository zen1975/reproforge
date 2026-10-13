"""B arm (free-generation baseline analogue) for jev-live-systemone-check-v3a.

B is NOT the paper's B (its prompt is not available to this study): it is an analogue built from the
paper's description. Same model as the C control (claude-haiku-5-5) so B-vs-C isolates the interface
(free generation with a short rationale vs a forced enum choice over a rotated candidate list) and
C-vs-J isolates the decision model. B sees a fixed-order command reference WITH descriptions and no
`abstain` token; its prompt does not depend on the candidate order (order_idx rows are replicates).
Facts as in jev_v2_arms.py: sampling parameters are omitted (the model rejects non-default values), so B
is stochastic; pricing $0.10 / $0.50 per MTok.

choose(state, instructions, criteria, oracle=None) matches the v2 selector interface; `oracle` is ignored
and never reaches a prompt.
"""
from __future__ import annotations

import re
import time

import jev_v2_arms as v2arms
import jev_v2_core as core

v1 = core.v1
B_MODEL = v2arms.CONTROL_MODEL
B_PRICING = v2arms.CONTROL_PRICING
B_MAX_TOKENS = 400
B_SYSTEM = (
    "You are the action selector in a software workflow. Think briefly (at most three sentences), then end "
    "your answer with exactly one final line of the form `ACTION: <command>` where <command> is one command "
    "name from the command reference. Write nothing after that line."
)
_ACTION_LINE = re.compile(r"^\s*ACTION:\s*(.+?)\s*$", re.I | re.M)
_STRIP = " \t`'\"*.,;:()[]<>"


def command_reference(criteria: dict) -> list[tuple[str, str]]:
    """Fixed alphabetical (name, description) list; the abstain token is not offered to B."""
    return sorted((n, d) for n, d in criteria.items() if n != core.ABSTAIN)


def build_b_request(state: str, instructions: str, criteria: dict, model: str = B_MODEL) -> dict:
    ref = "\n".join(f"- {n}: {d}" for n, d in command_reference(criteria))
    return {
        "model": model,
        "max_tokens": B_MAX_TOKENS,
        "system": B_SYSTEM,
        "output_config": {"effort": "low"},
        "messages": [{
            "role": "user",
            "content": f"{state}\n\n{instructions}\n\nCommand reference:\n{ref}",
        }],
    }


def parse_action(text: str, allowed) -> str | None:
    """Last `ACTION:` line, stripped of quotes/backticks/trailing punctuation; exact match or None."""
    matches = _ACTION_LINE.findall(text or "")
    if not matches:
        return None
    token = matches[-1].strip(_STRIP)
    return token if token in set(allowed) else None


class BArm:
    """Free-generation baseline analogue via the official Anthropic SDK (client injected for tests)."""

    def __init__(self, client, guard=None, model: str = B_MODEL, sleep=time.sleep):
        self.client, self.guard, self.model, self._sleep = client, guard, model, sleep

    def choose(self, state: str, instructions: str, criteria: dict, oracle=None):
        req = build_b_request(state, instructions, criteria, self.model)
        allowed = [n for n, _ in command_reference(criteria)]
        retries, waited = 0, 0.0
        while True:
            t0 = time.perf_counter()
            try:
                resp = self.client.messages.create(**req)
                latency = time.perf_counter() - t0
                break
            except Exception as exc:  # noqa: BLE001 - classified below, never swallowed silently
                if v2arms._retryable(exc) and retries < len(v2arms.RETRY_BACKOFF):
                    self._sleep(v2arms.RETRY_BACKOFF[retries])
                    waited += v2arms.RETRY_BACKOFF[retries]
                    retries += 1
                    continue
                return v1.make_decision(None, valid=False, infra=True, retries=retries, retry_wait_s=waited,
                                        error=f"{type(exc).__name__}:{getattr(exc, 'status_code', '')}"[:200])
        usage = {"input_tokens": getattr(resp.usage, "input_tokens", 0),
                 "output_tokens": getattr(resp.usage, "output_tokens", 0)}
        if self.guard:
            self.guard.charge(usage)
        text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", None) == "text")
        choice = parse_action(text, allowed)
        valid = choice is not None
        d = v1.make_decision(
            choice, valid=valid, latency_s=latency, usage=usage,
            model=getattr(resp, "model", None), retries=retries, retry_wait_s=waited,
            error=None if valid else "no_parsable_action",
        )
        d["stop_reason"] = getattr(resp, "stop_reason", None)
        d["request_id"] = getattr(resp, "_request_id", None)
        return d
