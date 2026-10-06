# Capability Agent Guide — Trajectory Budget Serializer

- Status: experimental
- Source study: `studies/arxiv-2610.03315`

## Contract
This core allocates a fixed serialization budget. It is deterministic and must remain usable without an LLM.

## Lightweight checks
Test total allocation never exceeds budget, warning/error floors, deterministic ties, zero/short trajectories, oversubscribed floors, and late-failure preservation.

## Heavy/local work
Learned/MMR selectors and judge models belong in the source study until their protocol is verified.

## Real implementation
Keep selection, budget allocation, and judging as separate layers. Never hide an LLM call inside the deterministic serializer.
