# ReproForge

Open research infrastructure for independently reproducing computational and AI research with explicit provenance, deterministic experiments, and machine-checkable evidence.

ReproForge is **not** a mirror of papers, author code, datasets, or model weights. It is a neutral framework for defining, running, and auditing independent reproduction studies.

## Core workflow

```text
Paper / Research Claim
        ↓
Paper Manifest
        ↓
License & Asset Gate
        ↓
Reproduction Spec
        ↓
Environment Freeze
        ↓
Experiment Runner
        ↓
Evidence Bundle
        ↓
Verdict: PASS / PARTIAL / FAIL / INCONCLUSIVE
```

## Design principles

1. **Independent by default** — implementations should be written from the paper or research description unless use of official code is explicitly declared.
2. **Provenance first** — every external codebase, dataset, model, weight, artifact, and paper source must be declared.
3. **Fail closed on licensing** — unknown or incompatible licensing blocks redistribution and may block execution depending on policy.
4. **Environment is evidence** — runtime, dependency, hardware, seed, and configuration metadata are part of the result.
5. **Claims, not vibes** — conclusions are tied to explicit claims and measurable acceptance criteria.
6. **Negative results matter** — failed and partial reproductions are valid research outputs when evidence is preserved.
7. **Machine-checkable where possible** — schemas, tests, hashes, and structured reports are preferred over narrative-only claims.

## Status

`v0.1.0-dev` — initial research harness and protocol definition.

## Repository layout

```text
reproforge/
├── src/reproforge/            # Core library
├── schemas/                   # Machine-readable contracts
├── templates/                 # Reproduction study templates
├── tests/                     # Determinism and protocol tests
├── docs/                      # Research protocol and policy
├── .github/workflows/         # CI validation
├── pyproject.toml
├── Dockerfile
└── Makefile
```

## What belongs here

- Reproduction manifests and schemas
- Environment capture and hashing
- Evidence recording
- Determinism checks
- Claim-level verdict logic
- Reporting and validation tools

## What does not belong here by default

- Full paper PDFs or copied paper text
- Copyrighted figures copied from papers
- Third-party source code without compatible licensing
- Datasets whose license does not permit redistribution
- Model weights without explicit redistribution rights
- API keys, credentials, private datasets, or personal data

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Validate an example manifest:

```bash
reproforge validate templates/paper-manifest.example.yaml
```

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

See [`docs/REPRODUCTION_PROTOCOL.md`](docs/REPRODUCTION_PROTOCOL.md) and [`docs/LICENSE_POLICY.md`](docs/LICENSE_POLICY.md).

## License

ReproForge itself is licensed under the Apache License 2.0. Individual reproduction studies and third-party assets may have different licenses and must declare them separately.

## Disclaimer

ReproForge is research infrastructure, not legal advice. Users remain responsible for complying with licenses, terms, privacy obligations, export controls, patents, and other applicable rules for the assets they use.
