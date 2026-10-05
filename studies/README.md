# Studies

Each directory under `studies/` is an independent reproduction study for one paper, method, or research claim set.

Recommended layout:

```text
studies/<study-id>/
├── manifest.yaml
├── claims.yaml
├── experiments/
├── evidence/
└── report.md
```

A study must not silently inherit licensing assumptions, datasets, code, weights, or claims from another study. Shared reusable logic belongs in `capabilities/` only after promotion criteria are met.

One repository can therefore contain many papers without mixing their evidence or provenance.
