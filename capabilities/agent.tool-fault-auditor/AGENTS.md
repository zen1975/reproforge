# Agent Guide — Tool Fault Auditor

## Current scope
Provider-neutral, deterministic, independent synthetic fault injection and metric scaffolding. Experimental only.

## Heavy/local
Paper-scale model trajectories and external datasets belong in `studies/arxiv-2610.10062`, not this capability directory.

## Real implementation
Tool state remains executor-owned. A silent corrupted return must not mutate the underlying state beyond the legitimate call.
Do not infer model detection from scripted policies. Preserve the distinction between detection, replanning, recovery and repetition.
