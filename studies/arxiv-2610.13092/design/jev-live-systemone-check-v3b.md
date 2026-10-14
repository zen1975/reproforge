# Design: jev-live-systemone-check-v3b (one fixed auxiliary-overhead experiment)

Status: **implemented offline; not run.** Written while the v3a test was running and before any v3a test result was seen, so nothing below can depend on v3a outcomes. v1, v2 and v3a (code, generator g2, pins, evidence) stay frozen; v3b imports them read-only. This is the "minimal v3b" of `design/jev-live-systemone-check-v3.md` (section 4, overhead module) cut down per the continuation directive: one small fixed experiment, no new families.

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
