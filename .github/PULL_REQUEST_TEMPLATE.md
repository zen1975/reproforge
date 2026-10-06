## ReproForge PR checklist

### Study / capability

- [ ] I identified the affected study/capability.
- [ ] I read the study's `status.yaml` and `HANDOFF.md`.
- [ ] I did not silently change a frozen held-out/blind evaluation.

### Provenance / claims

- [ ] Author-reported values are separated from ReproForge measurements.
- [ ] External code/data/models have provenance and license/access status.
- [ ] I did not invent unpublished prompts, coefficients, reward weights, mixture ratios, or decoding settings.

### Evidence

- [ ] New measurements have machine-checkable Evidence or an explicit reason why not.
- [ ] Seeds/configs/revisions/hardware are recorded where relevant.
- [ ] Large/gated assets are referenced rather than redistributed unless permission is explicit.

### Lifecycle

- [ ] `status.yaml` reflects the actual current lifecycle.
- [ ] If marking `HEAVY_COMPUTE_READY`, `free_light_phase_complete=true` and `handoff.ready=true`.
- [ ] `HANDOFF.md` contains the next command, prerequisites, frozen evaluations, expected outputs, known unknowns, and promotion rule.

### Verification

- [ ] `make verify` passes.
