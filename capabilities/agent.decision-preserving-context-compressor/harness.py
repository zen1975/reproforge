"""Provider-neutral FOCUS protocol harness.

Implements the published Algorithm 1 control flow while keeping draft-model
transport outside the capability. The caller provides token count and a draft
function; ReproForge provides prompt shape, strict parsing, N-rollout aggregation,
threshold selection, and defensive rescue union.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
import importlib.util
from pathlib import Path

CAP = Path(__file__).resolve().parent

PAPER_DRAFT_SYSTEM_PROMPT = """You are a planning assistant performing Dual-Objective Defensive Drafting.
Given a partially completed task and the executor's workspace trace, your goal is twofold:
1. OPTIMISTIC PLANNING: Generate a high-level plan sketch for completion. For each step, cite the exact historical spans you depend on.
Format: Step: <description> | Depends on: [s_X, s_Y]
2. PESSIMISTIC VERIFICATION: Review all remaining, un-cited spans in the trace. If discarding an un-cited span would cause the executing agent to blindly repeat a mistake or lose causal state, you MUST rescue it.
Format: Rescued Spans: [s_A, s_B] | Reason: <risk if deleted>"""


@dataclass(frozen=True)
class ProtocolRun:
    compression_triggered: bool
    draft_calls: int
    retained_ids: tuple[str, ...]
    dropped_ids: tuple[str, ...]
    utility: dict[str, float]
    rescued_ids: tuple[str, ...]
    raw_outputs: tuple[str, ...]


def _load(name: str):
    path = CAP / name
    spec = importlib.util.spec_from_file_location(f"focus_{name}", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_trace(goal: str, spans: Sequence) -> str:
    lines = [f"Task: {goal}", "", "Workspace trace:"]
    for span in spans:
        lines.append(
            f"[{span.id}] | Thought: {span.reasoning} | "
            f"Action: {span.action} | Observation: {span.observation}"
        )
    return "\n".join(lines)


def run_focus(
    spans: Sequence,
    *,
    goal: str,
    context_tokens: int,
    memory_budget_tokens: int,
    draft: Callable[..., str],
    rollouts_n: int = 3,
    tau: float = 0.3,
    draft_temperature: float = 0.7,
    seed: int = 42,
) -> ProtocolRun:
    if memory_budget_tokens < 1:
        raise ValueError("memory_budget_tokens must be >= 1")
    if context_tokens < 0:
        raise ValueError("context_tokens must be >= 0")
    if rollouts_n < 1:
        raise ValueError("rollouts_n must be >= 1")

    ids = tuple(span.id for span in spans)
    if context_tokens <= memory_budget_tokens:
        return ProtocolRun(
            compression_triggered=False,
            draft_calls=0,
            retained_ids=ids,
            dropped_ids=(),
            utility={span_id: 1.0 for span_id in ids},
            rescued_ids=(),
            raw_outputs=(),
        )

    parser = _load("parser.py")
    core = _load("compressor.py")
    user_prompt = render_trace(goal, spans)

    dependencies = []
    rescued = set()
    outputs = []
    for rollout in range(rollouts_n):
        text = draft(
            system_prompt=PAPER_DRAFT_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            temperature=draft_temperature,
            seed=seed + rollout,
        )
        deps, rescue = parser.parse_plan(text)
        dependencies.append(deps)
        rescued |= rescue
        outputs.append(text)

    result = core.compress(
        spans,
        dependencies,
        tau=tau,
        rescued_ids=rescued,
    )
    return ProtocolRun(
        compression_triggered=True,
        draft_calls=rollouts_n,
        retained_ids=result.retained_ids,
        dropped_ids=result.dropped_ids,
        utility=result.utility,
        rescued_ids=result.rescued_ids,
        raw_outputs=tuple(outputs),
    )
