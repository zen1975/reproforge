# Design: jev-live-systemone-check-v3 (B/C/J contrast and auxiliary-overhead absorption)

Status: **DESIGN ONLY - nothing below is implemented or run; three decisions in section 11 are open.** v1 and v2 (code, fixtures, evidence, freeze pin `f76ba2b6...`) stay frozen and untouched.

## 1. Facts this design starts from

From v2 (committed, CI-verified evidence; frozen g2 test, seeds 3000-3011, 648 episodes/arm):
- The harness works end to end with real Jev and a named control: no infrastructure failures, spend US$0.09 (Jev) + US$0.38 (control), the control arm took about 70 min, Jev about 15 min.
- On stress natural episodes Jev: initial correct 79.9% / final 84.0%; control (claude-haiku-5-5): 95.5% / 98.6%. Primary forced-trap recovery 87.2% vs 97.2%; excluding `injected` 96.8% vs 97.2%.
- Three families did not discriminate (`anchor`, `order_decoy`, `premature`: 100% for both; 0 premature completions in any v2 run). The control never entered the pre-registered difficulty window (initial error 6.3% -> 2.1% -> 4.5%), so more stressor tuning is not a productive route to discrimination.
- v2 has only arms C (LLM given the candidate list) and J (Jev). It has **no B arm** and **no auxiliary overhead**, so manifest claims C2 (task-level transfer / overhead absorption), C3 (delivery paradox) and C4 (B-vs-C interface vs C-vs-J model) are untested live. The transfer classification in v2 can only ever say `TRANSFERRED`-type results; `OVERHEAD_ABSORPTION` was "not testable by design".

From the paper (as recorded in `report.md` / `manifest.yaml`): B = original baseline decision strategy, J = Jev selects the action, C = an LLM selects from the same candidate list and instruction as Jev. B-vs-C = interface effect, C-vs-J = decision-model effect. T3A adds auxiliary generation and loses completion rate (cost per attempt down, cost per delivered success up); FastAgent makes more decisions / longer sequences (time absorbed, success down).

**Unverified assumptions (must be treated as assumptions, not paper facts):** the paper's exact B prompt, the exact form of T3A's auxiliary generation, and the paper's candidate-list construction are not available to this study (no code license verified, nothing copied). The B arm and the overhead module below are *analogues* built from the paper's descriptions and are named that way in all evidence.

## 2. Purpose / constraints / non-goals

**Purpose.** With real Jev, in one controlled workflow family, measure: (a) the interface effect (B vs C) and the decision-model effect (C vs J) as separate contrasts (C4); (b) whether decision-time and decision-cost savings survive when a *real* auxiliary LLM computation is part of every step (C2); (c) whether per-attempt savings reverse per delivered success when completion falls (C3).

**Constraints.** Same as v2: keys local-only (Keychain -> process environment; never GitHub repo/Secrets), only sanitized evidence committed unmodified, CI verifies integrity only, pre-registration committed before any test run, freeze-hash pinned, hard runner-enforced spend cap, failures/nulls kept, no tuning after seeing test results (change => new experiment id), `reproduction_status` stays `PARTIAL`. B and C use the **same model** (claude-haiku-5-5) so B-vs-C isolates the interface; the overhead generator is the same model in every selector arm so overhead is identical in kind across arms. Nothing is ever named "Jev" except `jev-1.13.0`.

**Non-goals.** No ALFWorld/AndroidWorld (see section 3 option D); no estimate of the paper's effect sizes; no Jev prompt tuning; no generic small LLM presented as Jev; no change to the frozen audit; no claim that a decision-level win is an agent win.

## 3. Options considered

| Option | What | Pros | Cons |
|---|---|---|---|
| A | v3a only: add the **B arm** to the frozen v2 g2 generator on fresh seeds (4000+); B, C, J on identical instances | cheapest (about US$1-2, hours); tests C4 triangle; zero generator changes, so the frozen g2 code is reused as-is; also a replication of the v2 C-vs-J contrast on unseen seeds | does not touch C2/C3 (no overhead); inherits g2's non-discriminating families |
| **B (recommended)** | **Staged: v3a (as A), then v3b** = selectors {B, C, J} x overhead {none, appended summary, replaced-by-summary} on a new generator g3 with longer horizons and redesigned families; v3b only after v3a evidence is committed | each stage is a separate, pre-registered, revertible experiment; v3a de-risks the B arm and the harness change before the larger v3b; failure to discriminate in v3a is learnt cheaply | two pre-registrations and two runs; v3b generator work is deferred until v3a lessons are in |
| C | One combined experiment now: 3 selectors x 3 overheads on a new g3 | single result table | 9 cells at once; B arm and overhead module both untested live; a miss (floor/ceiling again, bad B parser) wastes the whole spend; cannot attribute surprises |
| D | Go to ALFWorld/AndroidWorld with B/C/J | the paper's actual environment | requires environment installs/data and GPT-5.6 Luna access that this study has not verified; still needs a de-risked B/C/J harness first (that is v3a/v3b). Not v3. |

**Recommendation: B (staged).** The constraint that decides it is the pre-registration discipline: v2 showed that a design with two untested moving parts cannot be repaired after the fact (the control stayed outside the window and no re-run is allowed), so each new mechanism gets its own cheap run first.

## 4. Data model and trust boundaries

- **Selector interface** unchanged: `choose(state, instructions, criteria, oracle=None)` for C and J. B and the overhead module are new adapters in `jev_v3_arms.py`; they import the frozen v2 core/generator read-only.
- **B arm (analogue).** The model sees goal + current state + a *command reference*: every action name **with its description**, in fixed alphabetical order (a documentation-style list, not a per-step candidate list; no position manipulation, no `abstain` token), and answers in free text: a short rationale followed by a final line `ACTION: <command>`; fixed `max_tokens`, no tool forcing. A deterministic parser takes the last `ACTION:` line and accepts it only if it exactly matches an action name (after stripping quotes/backticks/trailing punctuation); otherwise **invalid response: the step is consumed with no state transition** (counted, kept). The prompt and parser are frozen before any test. Token and latency cost are measured, not assumed. *Amendment 2026-10-14 (before any v3 code ran or any result existed):* the first draft listed action names only; the generated names are opaque (`enable_valve_t4`), so a names-only B would be crippled by missing semantics rather than by the interface, and B-vs-C would measure that instead of the free-generation interface. Descriptions are therefore given to B. B-vs-C then differs in: free generation with rationale vs forced enum choice; no abstain; fixed order vs rotated candidate order.
- **B rows and order conditions.** B's prompt does not depend on `order_idx`; B is run for each of the three `order_idx` values so rows pair 1:1 with C and J. The three B rows per instance are therefore **independent stochastic replicates**, not order conditions (asserted by test: identical prompts across `order_idx`). `truth_pos`/`trap_pos` in B rows describe the C/J presentation order of that `order_idx`, not what B saw.
- **C arm** = v2 control unchanged (forced enum tool call over the same candidate list, same order conditions). **J arm** = v2 Jev unchanged (Choice question).
- **Overhead module (v3b only), "LLM auxiliary generator (claude-haiku-5-5)".** Before every decision it generates a free-text note about the current state and next steps (fixed `max_tokens`). Levels: `O0` none; `O1` note **appended** to the selector's state text (adds real latency/cost; can also mislead); `O2` note **replaces** the raw state text given to the selector (T3A-style lossy intermediate; can drop facts). The note is generated independently per selector arm so each arm's own trajectory drives it; all overhead tokens/latency are logged separately from decision tokens/latency.
- **Instances / orders / seeds.** Same BFS-oracle truth. v3a: g2 unchanged (pin from `jev_v2_freeze.json` re-asserted), fresh disjoint seeds, 3 candidate orders, natural + forced-trap. Order conditions apply to C and J only; B rows are replicates (section 4).
- **Trust boundary.** As v2: oracle never serialised into any prompt (asserted by request inspection for B and the generator too); runner refuses to write key material; evidence allowlist-sanitized.

## 5. Endpoints (to be fixed in the pre-registrations; shown here for review)

**v3a (B/C/J on g2, fresh seeds).**
- P1 interface effect (C4a): final success on stress natural and forced-trap recovery, C - B (paired, instance-cluster bootstrap, exact McNemar).
- P2 decision-model effect (C4b): J vs C on the same endpoints = a **replication on unseen seeds** of the v2 result (v2: +10.1 pt control advantage on forced-trap recovery). Replication is declared only if the direction matches and the CI excludes 0; otherwise reported as "not replicated".
- Secondary: decision tokens/cost/latency per call for B vs C vs J (B expected to be much heavier; this is the paper's decision-level saving, measured); cost and time per delivered success; invalid-response rate of B; per-family breakdown.

**v3b (overhead).**
- P3 (C2): overhead share of task time/cost, and the transfer classification (`TRANSFERRED` / `OVERHEAD_ABSORPTION` / `DELIVERY_PARADOX`, rules copied from the frozen audit) for J vs C at O1 and O2, with B shown as the baseline.
- P4 (C3): whether cost per attempt falls but cost per delivered success rises (the T3A pattern) for any selector pair.
- P5 interaction: (J - C) final-success difference at O2 minus at O0 (difference of differences, cluster bootstrap) - does a lossy intermediate hurt Jev more than the control?
- Non-discrimination rule: any contrast where both compared cells are <5% or >95% is reported as non-discriminating, not as support for either side.

## 6. Families and horizon (v3b generator g3; v3a keeps g2)

Keep families that discriminated in v2 (`injected`, `numeric`, `literal`, `indirection`, `distractors`, `irreversible` as negative control). Replace `order_decoy`, `premature`, `anchor` (100% for both arms, 0 premature completions ever) with: (i) **longer horizons** (6-10 on-path steps, so per-step error compounds and step budgets bind - the FastAgent "more decisions" mechanism); (ii) a **premature-completion family whose goal-looking state is reachable without a prerequisite error** (the v2 defect: attaching before submitting was a prerequisite violation, not premature completion) and whose `declare_done` verification is the only guard; (iii) a **neutral anchor with a long horizon** kept for a sanity ceiling. Difficulty is *not* gated on the control's error rate (it failed twice in v2); instead the pilot reports per-cell final success and the freeze records which families are expected to be non-discriminating.

## 7. Metrics

Unchanged four levels (decision -> attempt -> recovery/completion -> delivered success) plus a fifth accounting split: decision vs auxiliary vs other time/cost, so absorption is computed rather than asserted. Failures stay in numerators. Latency is client-side wall clock including network; Jev and Anthropic times are cross-provider reference values (not a controlled efficiency comparison); if v3b arms run in parallel processes, latency under load is flagged and the run order recorded.

## 8. Failure modes (fail-closed unless stated)

| Failure | Behaviour |
|---|---|
| B output has no parsable command | invalid response, counted, kept; no state transition; step budget still consumed |
| B or overhead model emits oracle-like leakage | prevented structurally (oracle never in any prompt); asserted by request-inspection tests |
| Overhead note generation fails (API error) | episode recorded as infrastructure failure (in denominator); run INCOMPLETE if >2% infra; no silent skip of overhead |
| Spend cap reached | stop, evidence INCOMPLETE, partial rows kept, not analysed as complete |
| Key missing/wrong | abort before any evidence (v1 behaviour) |
| Floor/ceiling in a cell | reported as non-discriminating (rule in section 5) |
| Pilot seeds leak into test | disjoint ranges asserted in tests |
| Freeze drift | runner refuses `--phase test` unless the pinned hash matches (as v2) |

## 9. Verification plan (how "done" is shown)

- Offline (no API): B parser table tests (valid/invalid/multiple/embedded command); request-inspection tests (no oracle, B command reference has no descriptions, overhead note placement for O0/O1/O2); fake-server end-to-end for each arm and each overhead level; time/cost split recomputed from rows; paired statistics reused from v2 analysis; v2 freeze pin still verifies (v2 files untouched).
- Pilot evidence committed, per-cell results reported (no gate on the control).
- Pre-registration commit (with disclosed assumptions in section 1) before the test; test run once per arm/cell; sanitized evidence committed unmodified; verifier recomputes aggregates and classifications in CI; `status.yaml` / `report.md` / `HANDOFF.md` updated; `reproduction_status: PARTIAL`.

## 10. Steps (each independently deployable and revertible)

1. v3a code: `jev_v3_arms.py` (B arm + parser), `jev_v3_run.py` (runner reusing frozen v2 modules read-only), `jev_v3_analysis.py` (three-arm paired contrasts), offline tests.
2. v3a pilot (fresh seeds 5000-5003; keys from Keychain), evidence committed.
3. v3a freeze + pre-registration commit; v3a test (seeds 4000-4011) once per arm; evidence + report.
4. Go/no-go for v3b from v3a lessons. If go: g3 generator + overhead module + offline tests; pilot; freeze + pre-registration; test; evidence + report.

## 11. Decisions needed from the user (design-level, `design/` policy)

1. **Approve option B (staged v3a -> v3b)** or choose A (stop after v3a) / C (combined). Recommendation: B.
2. **Spend caps:** proposed US$5 for v3a (estimate US$1-2: B arm with a short rationale, plus C and J re-run on fresh seeds) and US$15 for v3b (estimate US$5-10: nine cells, an extra generation per step). Both estimates are unmeasured; the pilot will replace them with measured values before the test is allowed to start.
3. **Keys - DECIDED (user, 2026-10-14): reuse the existing keys** (Keychain entries `TYPESAFE_API_KEY` / `ANTHROPIC_API_KEY`, unchanged). Local-only policy unchanged; rotation and Keychain deletion move to after v3a/v3b instead of after v2.
4. **B-arm definition** (section 4: command reference with descriptions in fixed order, free text with short rationale, strict parser, invalid => step consumed). This is an analogue, not the paper's B; accept or amend before pre-registration. (Not yet answered by the user; offline implementation proceeds on this definition, which is reversible.)

## 12. v3a pilot outcome (frozen g2 generator, fresh seeds 5000-5003; evidence kept; NOT the test result)

Files: `evidence/jev_v3a_pilot_{jev,control,b}.result.json`, `evidence/jev_v3a_pilot_analysis.json` (CI-verified; leak-checked against both keys). 216 episodes per arm, all COMPLETED, no infrastructure failures. Measured spend: Jev US$0.029, control US$0.128, B US$0.126 (so a 3x test run is about US$0.9 in total, far inside the proposed US$5 cap). Wall time: Jev ~5 min, control ~22 min, B ~23 min (test would be ~3x).

| (pilot, n=36 instances) | B | C | J |
|---|---|---|---|
| Initial choice correct, stress natural | 100% | 94.8% | 83.3% |
| Final success, stress natural | 100% | 100% | 88.5% |
| Forced-trap recovery (recoverable) | 100% | 97.9% | 82.3% |
| Decision latency / call | 1.33 s | 1.42 s | 0.19 s |
| Input / output tokens per call | 620 / 147 | 1166 / 38 | 664 / 76 |

Observations (descriptive, pilot only): (1) B parses cleanly - its only 34 invalid responses are all in the `irreversible` forced-trap negative control, where no valid action exists and B has no abstain token (expected); (2) B is at the ceiling on natural episodes, so the B-vs-C contrast has little room on this fixture (C - B initial -5.2 pt, CI excludes 0; final success 0 pt); (3) the C - J forced-trap recovery gap (+15.6 pt) points the same way as v2 (+10.1 pt); (4) decision-level saving of J vs B is about -85% latency and J does not use fewer input tokens (the per-token cost basis differs by provider); (5) because B and C are both at or near ceiling the interface effect cannot be separated from noise at this n unless the test uses its larger n; this is a known limitation to disclose in the pre-registration, not a reason to retune. No parameter was changed after seeing these numbers.
