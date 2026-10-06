# Study: arXiv 2610.06191

**Paper:** Judged Useless, Queried Anyway: Tool-Using Agents Rarely Turn Their Own Evidence Judgments into Stopping Decisions  
**arXiv:** https://arxiv.org/abs/2610.06191  
**Intake:** VERIFIED against authoritative arXiv metadata and full PDF  
**Reproduction:** PARTIAL  
**Lifecycle:** PROTOCOL_VERIFIED

## Why this study

The paper identifies a reusable systems problem: an agent can correctly judge repeated tool evidence as useless and still continue calling the tool. Prompting changes stopping behavior only partially; the paper's strongest intervention moves the integration step into the harness.

The reusable capability hypothesis is:

`agent.evidence-aware-stopping-gate`

This fits ReproForge's separation between model judgment and deterministic system policy.

## Verified paper mechanism

The paper's enforced integration rule tracks the current run of consecutive USELESS judgments. After five consecutive useless results, the harness removes further search/lookup actions and forces the answer action. A useful result resets the run. The paper evaluates this under controlled source failures and includes pre-registered held-out replication.

The paper reports that tested agents judged failing-source results useless 97–100% of the time while usually continuing to query. Those are **paper-reported values**, not ReproForge reproduction results.

## ReproForge mechanism evidence

ReproForge implements a separate deterministic gate from the paper description and runs a frozen synthetic benchmark covering:

- persistent source failure;
- recovery before the threshold;
- intermittent usefulness;
- exact threshold firing;
- sticky post-fire behavior;
- tool-call savings relative to a deadline-only baseline.

This initial experiment verifies only the harness mechanism. It does not reproduce the paper's model behavior, HotpotQA/FEVER environments, time-matched contrast, or reported success statistics.

## Time-matched contrast protocol verification

ReproForge now includes its own executable implementation of the paper-defined time-matched stopping contrast Δ. A frozen synthetic protocol test produces the expected behavior:

- evidence-integrating stopping: Δ = 1.0
- clock-matched stopping: Δ = 0.0

The implementation was then audited against the authors' released CC BY 4.0 episode data at pinned repository commit `2e6404e542b4afdafa3d54d9b18eb1c28c2bafc8`.

Across **all 43 released cells with available episodes**, ReproForge reproduced the stored paper values exactly:

- Δ exact matches: 43 / 43
- 95% bootstrap interval exact matches: 43 / 43

Representative Qwen3-8B results:

- test300 unaided: Δ = -0.0648006045
- test300 enforced rule: Δ = +0.3290158752
- fresh300 unaided: Δ = -0.0520519898
- fresh300 enforced rule: Δ = +0.3444698781

This is an `OFFICIAL_AUDIT` of released trajectories using a separate ReproForge metric implementation. It does **not** independently regenerate the model trajectories.

## External assets

The official repository is public and MIT-licensed. Its released episode data is documented as CC BY 4.0. ReproForge does not vendor either into this study. Because the official repository was inspected before implementation, this study is classified as `DERIVED`, not clean-room independent.

## Next gate

Audit the remaining lightweight paper summaries (answer-after-five-useless and released success-rate aggregates). After that, if remaining work is primarily original large-model episode regeneration, move the study to `HEAVY_COMPUTE_READY` with a fork-ready handoff.
