# ReproForge

**Reproduce, verify, and operationalize research as reusable capabilities.**

ReproForge is open research infrastructure for turning computational and AI research into independently verified, reusable capabilities with explicit provenance, deterministic experiments, and machine-checkable evidence.

ReproForge is **not** a mirror of papers, author code, datasets, or model weights. It is a neutral framework for reproducing research, preserving evidence, and promoting verified methods into stable capability contracts that can later be exposed through CLI, Python, HTTP, MCP, agent tools, Workers, or other adapters.

## Core workflow

```text
Paper / New Method
        ↓
Study Manifest
        ↓
License & Asset Gate
        ↓
Claim-level Reproduction
        ↓
Environment Freeze
        ↓
Evidence Bundle
        ↓
Lifecycle:
INTAKE_VERIFIED → MECHANISM_VERIFIED → PROTOCOL_VERIFIED
→ HEAVY_COMPUTE_READY → REPRODUCED
        ↓
Verdict: PASS / PARTIAL / FAIL / INCONCLUSIVE
        ↓
Capability Extraction
        ↓
Stable Capability Contract
        ↓
Registry
        ↓
Adapters / Plugins / Runtimes
```

## One repository, many papers

ReproForge is intentionally a monorepo for many independent reproduction studies.

```text
studies/
  <paper-or-study-id>/
    manifest.yaml
    claims.yaml
    experiments/
    evidence/
    status.yaml
    HANDOFF.md
    report.md

capabilities/
  <capability-id>/
    capability.yaml
    implementation/
    tests/

registry/
  capabilities.json
```

A study remains isolated under `studies/`. A method is promoted into `capabilities/` only after its evidence and interface are explicit. Multiple papers may support the same capability, and one paper may produce multiple capabilities.

## Design principles

1. **Independent by default** — implementations should be written from the paper or research description unless use of official code is explicitly declared.
2. **Provenance first** — every external codebase, dataset, model, weight, artifact, and paper source must be declared.
3. **Fail closed on licensing** — unknown or incompatible licensing blocks redistribution and may block execution depending on policy.
4. **Environment is evidence** — runtime, dependency, hardware, seed, and configuration metadata are part of the result.
5. **Claims, not vibes** — conclusions are tied to explicit claims and measurable acceptance criteria.
6. **Negative results matter** — failed and partial reproductions are valid research outputs when evidence is preserved.
7. **Capability before plugin** — the stable contract is canonical; integrations are adapters, not the source of truth.
8. **Promotion requires evidence** — research code does not become a reusable capability merely because it runs once.
9. **Many papers, one registry** — studies are independent, capabilities are reusable, and the registry connects them.
10. **Machine-checkable where possible** — schemas, tests, hashes, and structured reports are preferred over narrative-only claims.

## Status

`v0.2.0-dev` — multi-paper study layout and capability-registry foundation.

## Repository layout

```text
reproforge/
├── studies/                    # Independent reproduction studies, one directory per paper/study
├── capabilities/               # Promoted reusable capabilities
├── registry/                   # Machine-readable capability index
├── src/reproforge/             # Core library
├── schemas/                    # Machine-readable contracts
├── templates/                  # Study and capability templates
├── tests/                      # Determinism, schema, and registry tests
├── docs/                       # Research and capability protocols
├── .github/workflows/          # CI validation
├── pyproject.toml
├── Dockerfile
└── Makefile
```

## Capability model

A capability is not tied to a single transport or product. Its canonical definition includes:

- stable ID and semantic version,
- purpose and task class,
- JSON-schema-like input/output contracts,
- runtime requirements,
- determinism declaration,
- source studies and evidence status,
- implementation location,
- adapter declarations.

Adapters may expose the same capability through Python, CLI, HTTP, MCP, Cloudflare Workers, or another agent/tool protocol without changing the underlying capability contract.

See [`docs/CAPABILITY_MODEL.md`](docs/CAPABILITY_MODEL.md).

## Quick start

Fork or clone, then:

```bash
python -m venv .venv
source .venv/bin/activate
make bootstrap
make verify
```

Inspect a study before continuing it:

```bash
reproforge study-status studies/arxiv-2610.03213
```

A study marked `HEAVY_COMPUTE_READY` has completed the project's free/lightweight phase. Read that study's `HANDOFF.md` before spending GPU time or changing a frozen evaluation.

Validate an example paper manifest:

```bash
reproforge validate templates/paper-manifest.example.yaml
```

See [`docs/STUDY_COMPLETION_POLICY.md`](docs/STUDY_COMPLETION_POLICY.md) for the standard stopping rule and fork handoff contract.

## What belongs here

- Reproduction manifests and schemas
- Multiple independent paper studies
- Environment capture and hashing
- Evidence recording
- Determinism checks
- Claim-level verdict logic
- Capability contracts
- Registry metadata
- Adapter definitions
- Reporting and validation tools

## What does not belong here by default

- Full paper PDFs or copied paper text
- Copyrighted figures copied from papers
- Third-party source code without compatible licensing
- Datasets whose license does not permit redistribution
- Model weights without explicit redistribution rights
- API keys, credentials, private datasets, or personal data

## Research use

Each reproduction study should state:

- the original paper and canonical URL,
- the paper license when known,
- whether implementation is independent or derived,
- all external assets and their licenses,
- exact claims being tested,
- acceptance criteria,
- environment metadata,
- random seeds,
- raw and derived evidence,
- final claim-level verdicts.

A capability promoted from one or more studies must additionally state its stable interface, implementation, evidence references, runtime constraints, and adapter surface.

See [`docs/REPRODUCTION_PROTOCOL.md`](docs/REPRODUCTION_PROTOCOL.md), [`docs/LICENSE_POLICY.md`](docs/LICENSE_POLICY.md), and [`docs/CAPABILITY_MODEL.md`](docs/CAPABILITY_MODEL.md).

## License

ReproForge itself is licensed under the Apache License 2.0. Individual reproduction studies and third-party assets may have different licenses and must declare them separately.

## Disclaimer

ReproForge is research infrastructure, not legal advice. Users remain responsible for complying with licenses, terms, privacy obligations, export controls, patents, and other applicable rules for the assets they use.
