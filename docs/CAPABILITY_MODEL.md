# Capability Model

## Purpose

ReproForge does not stop at reproducing research. Its second role is to convert sufficiently understood and evidenced methods into reusable system capabilities.

The canonical chain is:

```text
Research → Reproduction → Evidence → Capability → Adapter
```

A capability is transport-neutral. MCP, HTTP, CLI, Python, agent-tool protocols, and Cloudflare Workers are adapter surfaces rather than canonical definitions.

## Why this separation matters

Research implementations often contain notebook state, hard-coded datasets, temporary parameters, unavailable dependencies, benchmark-specific assumptions, or hardware coupling. Reusing that code directly creates fragile system dependencies.

ReproForge therefore separates:

1. **Study** — what was claimed and what was reproduced.
2. **Evidence** — what was measured and preserved.
3. **Capability** — the normalized reusable method with a stable contract.
4. **Adapter** — how another system calls the capability.

## Multi-paper model

The repository is designed to hold many studies:

```text
studies/paper-a/
studies/paper-b/
studies/paper-c/
```

A capability may cite several studies:

```text
paper-a ─┐
paper-b ─┼─> capability-x
paper-c ─┘
```

This allows independent replications, competing methods, extensions, and later papers to strengthen or weaken the evidence behind the same reusable capability.

## Promotion states

### experimental

The interface exists but the method has not met the project's verified promotion threshold.

### verified

The capability has an explicit contract and sufficient reproduction evidence under the project's protocol. `verified` is not a universal scientific truth claim; it means the declared evidence and acceptance criteria were satisfied.

### deprecated

The capability remains addressable for provenance and reproducibility but should not be selected for new integrations.

## Registry

`registry/capabilities.json` is the machine-readable index. It should contain only capability descriptors that validate against `schemas/capability.schema.json`.

The registry is intended to support future selection by compilers, agents, planners, and system runtimes.

## Adapter principle

Never make an integration protocol the source of truth.

```text
Capability Contract
├── Python adapter
├── CLI adapter
├── HTTP adapter
├── MCP adapter
├── Agent-tool adapter
└── Cloudflare Worker adapter
```

The capability remains stable even when adapter technologies change.

## Future selection

A future registry resolver may select capabilities using task class, runtime constraints, evidence strength, determinism, version, cost, latency, hardware, or licensing constraints. That selection layer should be deterministic and auditable where possible.
