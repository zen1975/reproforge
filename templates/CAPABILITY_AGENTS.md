# Capability Agent Guide

Replace bracketed fields when creating a new capability.

## Capability
- ID: `[capability-id]`
- Status: `[status]`
- Source studies: `[studies]`

Read `capability.yaml` and source-study `AGENTS.md` files before changing behavior.

## Lightweight verification
Keep a small deterministic smoke path and tests for the contract.

## Local/heavy verification
Training/benchmark-scale work belongs in the supporting study, not hidden inside the capability directory. Link resulting evidence back into `capability.yaml`.

## Real implementation
Preserve a provider-neutral core. Put transport/provider/runtime integrations behind adapters.

Do not strengthen the public contract beyond the evidence.
