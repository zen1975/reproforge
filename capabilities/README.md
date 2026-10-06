# Capabilities

`capabilities/` contains reusable implementations promoted from one or more reproduction studies.

A capability is the canonical unit of reuse. Plugins and protocol integrations are adapters around a capability, not the capability itself.

A capability should not be promoted merely because experimental code runs. Promotion requires:

- an explicit stable input/output contract,
- implementation location,
- runtime declaration,
- source study references,
- evidence status,
- licensing provenance,
- tests appropriate to the claimed guarantees.

Multiple studies may support the same capability. A single study may yield multiple capabilities.


## Agent continuation guide

Every capability directory must include `AGENTS.md`.

The capability guide defines:
- the stable contract;
- lightweight checks that must remain cheap and deterministic;
- which heavy/model work belongs back in the supporting study;
- the real implementation / operationalization boundary.

Read the source study's `AGENTS.md` and `HANDOFF.md` before changing evidence-backed behavior.

Use `templates/CAPABILITY_AGENTS.md` when creating a new capability.
