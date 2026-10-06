# Capability Agent Guide — Decision-Preserving Context Compressor

- Status: experimental
- Source study: `studies/arxiv-2609.37590`

## Contract
Retain/drop spans based on future-decision dependency evidence while preserving auditable IDs and dependency links.

## Lightweight checks
Always test deterministic selection, dependency closure/referential integrity, rescue behavior, boundary tau values, and empty/single-span trajectories.

## Heavy/local work
Large draft models and full agent benchmarks belong in the source study.

## Real implementation
Never return compressed context with dangling historical references. Dependency estimation may be learned; the final retained-span contract must remain inspectable.
