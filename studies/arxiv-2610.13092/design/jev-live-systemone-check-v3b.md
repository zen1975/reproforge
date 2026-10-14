# Design: jev-live-systemone-check-v3b (one fixed auxiliary-overhead experiment)

Status: **run once (frozen test, 2026-10-14); results in section 6.** Written while the v3a test was running and before any v3a test result was seen, so nothing below can depend on v3a outcomes. v1, v2 and v3a (code, generator g2, pins, evidence) stay frozen; v3b imports them read-only. This is the "minimal v3b" of `design/jev-live-systemone-check-v3.md` (section 4, overhead module) cut down per the continuation directive: one small fixed experiment, no new families.

## 1. Facts / purpose / constraints / non-goals

**Starting facts.** v2 (CI-verified) and the v3a pilot showed: Jev decision latency about 0.19 s vs about 1.4 s for the haiku arms; the haiku arms are at or near ceiling on the explicit families; Jev's reliability gap concentrates in `injected` (and `numeric`), while `indirection` did not hurt Jev. No auxiliary overhead has ever been present, so paper claims C2 (absorption) and C3 (delivery paradox) are untested live.

**Purpose.** Test the paper-C2/C3-style chain `local decision saving -> auxiliary overhead -> attempt cost/time -> final success -> cost/time per delivered success` with a **real** auxiliary LLM call in every step, for B / C / J on the same state machines.

**Constraints.** Same discipline as v2/v3a: keys local-only (Keychain), sanitized evidence committed unmodified, CI verifies integrity only, pre-registration + freeze pin committed before the test, spend caps enforced by the runner, failures/invalid/infra rows kept, no change after seeing results (=> new experiment id), `reproduction_status` stays `PARTIAL`. The auxiliary stage is identical in kind for every arm (same model, prompt, `max_tokens`).

**Non-goals.** No new families or generator changes, no more control models, no power escalation, no tuning of Jev, no ALFWorld/AndroidWorld, no claim about the paper's effect sizes. Not a test of whether Jev is accurate (v2/v3a did that).

## 2. Design

- **Families (fixed by the directive, three only):** `anchor` (clean/easy; Jev worked), `injected` (recovery-sensitive; where the v2 gap concentrated), `indirection` (Jev relatively strong). Frozen v2 generator g2 (`generate(seeds, families=...)`), fresh test seeds **6000-6011** (never used): 3 families x 12 = 36 instances x 3 order indices x {natural, forced_trap} = 216 episodes per cell. Disclosure: the family choice was informed by the (public, committed) v2 outcome; it was made before any v3a test result.
- **Arms:** B analogue, C control, J Jev, exactly as in v3a (unchanged adapters).
- **Overhead levels:** `O0` = no auxiliary stage (the same workflow as v3a); `O1` = **auxiliary stage on**. Cells: 3 arms x 2 levels = 6 independent processes, each run once.
- **Auxiliary stage (O1).** Before every *action* decision (not before completion verification) one `claude-haiku-5-5` call receives the same state text the selector would see and writes a note of at most three sentences: which goal conditions appear met or unmet and which prerequisites matter for the next step, **without recommending an action** (`max_tokens` 150, effort `low`, no tools, sampling parameters omitted). The note is appended to the state text the selector receives ("Assistant note about the state: ..."). It therefore adds real latency/tokens/cost to every arm and may also help or mislead the selector. This is a T3A-style auxiliary-generation analogue (the paper's exact T3A stage is not available); it is placed before the decision rather than between decision and transition because that is where a summary can influence the outcome; the directive's schematic order was an example. Forced first steps (harness action, no selector call) get no auxiliary call. An auxiliary API failure is an infrastructure failure of the episode (kept, in the denominator).
- **Accounting.** Per row: `decision_*` (selector only, unchanged definition), `aux_latency_total_s`, `aux_usage`, `aux_cost_usd`, `aux_calls`, and `workflow_latency_total_s` (wall clock incl. auxiliary). Task cost = decision + auxiliary cost; Jev decision cost = tokens x assumed US$0.042/Mtok (no cost field in the API).

## 3. Endpoints and classification (fixed now)

For each pair (J vs B, J vs C, C vs B) and each overhead level, on natural episodes: percentage change of *decision* latency/cost per call, *task* latency/cost per attempt (auxiliary included) and *delivered* time/cost per success (failures in the numerator); class from the frozen audit rule (`classify_transfer`): `NO_LOCAL_SAVING` if the decision delta >= 0, else `OVERHEAD_ABSORPTION` if the task delta >= 0, else `DELIVERY_PARADOX` if the delivered delta >= 0, else `TRANSFERRED`. Reported separately for time and cost. Also: auxiliary share of task time and cost per arm; paired instance-cluster contrasts (final success natural, forced-trap recovery, per family) per pair and level; and the auxiliary effect per arm (O1 vs O0 on identical instances; exact McNemar). Interpretation rules: decision-level advantage is not an agent advantage without delivered-success agreement; both-cells-at-floor/ceiling => non-discriminating; cross-provider speed/cost are reference values.

## 4. Failure modes

Auxiliary API error => episode infrastructure failure (kept); run INCOMPLETE if >2% infra; spend cap hit => INCOMPLETE and not analysed as complete; aux note containing oracle information is impossible by construction (the auxiliary call receives only the rendered state; asserted by request-inspection tests); freeze drift => runner refuses the test phase.

## 5. Verification and steps

Offline tests (fake clients): request inspection (aux sees only the state, no oracle, note appended only for action decisions), aux accounting separate from decision accounting, aux failure => infra, O0 == no aux calls, row grid, analysis recomputation, tamper detection, pin checks (v2 + v3a + v3b). Then: freeze + pre-registration commit; test run (6 processes); sanitized evidence + analysis + closure metrics committed; CI green; closure report. A tiny non-evidence live smoke (3 instances) checks the new request path before the freeze.

## 6. v3b frozen test outcome (seeds 6000-6011; pin `7876bc9b...`; pre-registered in `design/jev-live-systemone-check-v3b-preregistration.md`; run once per cell)

Files: `evidence/jev_v3b_test_{jev,control,b}_{O0,O1}.result.json`, `jev_v3b_test_analysis.json`, `jev_v3b_test_metrics.json` (CI re-derives and verifies). All six cells COMPLETED (216 episodes each), 0 infrastructure failures, 2 invalid responses (B, one per level); no key in evidence or logs. Spend: selector $0.036 / $0.037 (J O0/O1), $0.139 / $0.149 (C), $0.142 / $0.147 (B); auxiliary $0.102 / $0.086 / $0.086 (J / C / B O1).

| (natural final success; recoverable forced-trap recovery) | B | C | J |
|---|---|---|---|
| O0 | 100%; 100% | 100%; 99.1% | 70.4%; 69.4% |
| O1 | 100%; 100% | 100%; 100% | 72.2%; 77.8% |
| Delivered time per success (all episodes) O0 -> O1 | 7.70 -> 13.78 s | 7.53 -> 13.71 s | 2.00 -> 11.22 s |
| Aux share of task time at O1 | 43.9% | 46.6% | 84.9% |

- **Local saving vs delivered saving.** Decision latency per call is unchanged by the auxiliary stage (J about 0.20 s vs about 1.4-1.5 s for B/C). On natural episodes, J vs C: delivered time -73.0% at O0 but only -12.4% at O1; delivered total cost -61.9% at O0 and -13.8% at O1 (auxiliary cost included); the O1 absolute difference in delivered time per success (C minus J, +1.7 s) has a 95% CI of [-1.9, +4.7] s, i.e. not distinguishable from 0. Applying the frozen rule literally, J vs B and J vs C are `TRANSFERRED` (time and cost) at both levels, because the delivered deltas stay negative; C vs B is `NO_LOCAL_SAVING` (O0, time) / `OVERHEAD_ABSORPTION` (O1, time; about 2% differences). The strict rule therefore hides that most of Jev's delivered-time advantage was absorbed by the auxiliary stage (the fixed auxiliary latency of about 1.5 s per aux call, one per action decision is the same for every arm, so a faster selector saves a smaller fraction of a larger task); this is reported as partial absorption, not as a clean `OVERHEAD_ABSORPTION` class.
- **Reliability.** C minus J on recoverable forced-trap recovery: +29.6 pt (CI [14.8, 45.4], p = 4.1e-09) at O0 and +22.2 pt (CI [12.0, 34.3], p = 1.2e-07) at O1; on natural stress episodes +44.4 / +34.7 pt. Jev's failures stay concentrated in `injected` (natural success 11.1% at O0, 30.6% at O1; recovery 8.3% / 33.3%), while `anchor` and `indirection` are at 100% for Jev at O0. B and C are at or near 100% in every cell: the fixture is not sufficiently discriminative for B-vs-C.
- **Auxiliary effect (O1 vs O0, same instances).** B and C: no change (ceiling). Jev: recovery +8.3 pt (CI [2.8, 14.8], McNemar O1-only 10 / O0-only 1, p = 0.012), natural final success +1.9 pt (p = 0.80), but `anchor` natural dropped from 100% to 86.1% and overall initial-choice accuracy fell from 66.7% to 59.3%: the note helped some recoveries and misled some first choices. Not machine-checked that notes avoid recommending actions (disclosed).
- **Interpretation.** In this controlled analogue a large decision-latency advantage did not carry over one-to-one to delivered time/cost once a shared auxiliary stage was present, and delivered reliability remained concentrated in specific workflow conditions (`injected`). Not a reproduction of the paper's C2/C3; the auxiliary stage is an analogue; different providers, so speed/cost are reference values; three families and 12 instances each. `reproduction_status` stays PARTIAL.
