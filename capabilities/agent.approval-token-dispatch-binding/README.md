# Approval Token Dispatch Binding

Status: `experimental`  
Reproduction status: `NOT_RUN`

This capability is a provider-neutral contract extracted from the research questions in arXiv:2610.03213. It is not a copy of author code and is not yet a verified implementation.

## Intended behavior

Bind a tool invocation to authenticated dispatch context such as principal, agent/session identity, tool name, arguments, scope, and expiry. A mediator can issue a keyed approval token without exposing the signing key to the agent.

## Important limitation

A token can only bind what the mediator can actually observe and encode. If a harmful divergence occurs below that observation boundary while the bound fields remain identical, field-only verification cannot distinguish the safe and unsafe executions.

This limitation is part of the capability contract, not an implementation bug.

## Promotion gate

This capability may move from `experimental` to `verified` only after ReproForge independently reproduces the relevant positive and negative claims and stores machine-checkable evidence.

Source study: `studies/arxiv-2610.03213/`
