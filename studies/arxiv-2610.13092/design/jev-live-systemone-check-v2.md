# Design: jev-live-systemone-check-v2 (Jev vs LLM candidate-interface control)

Status: **DESIGN ONLY - nothing below is implemented or run.** v1 (`jev-live-systemone-check-v1`) stays frozen and untouched.

## 1. Facts this design starts from

From v1 (committed evidence, sha256 `35fa635c...325fdd`):
- Real Jev `jev-1.13.0` scored 36/36 (Test B) and 24/24 final success (Test C); 0 deviations, so recovery, premature completion and "better first decision but worse final" never occurred. The check was at **ceiling**.
- v1 had no control, a fixed (never shuffled) option order, small explicit states, hand-written cases only.
- Cost is negligible (about $0.0026 for 60 episodes); latency about 0.19 s/call. Cost is not the constraint, discrimination is.

From TypeSafe's own "Jev 1.13 jaggedness" page (reviewed 2026-10-02): `jev-1.13` is **literal**, weak on **indirection/multi-hop**, degrades with **large irrelevant state**, is **order-biased toward the first Choice option**, is unreliable on **counting/numbers/dates**, and can be steered by **adversarial content in state**. These are the documented places where first-decision errors should appear, so v2 targets them deliberately instead of hoping for errors.

From the paper (claims C1-C5 in `manifest.yaml`): the central contrast is C-vs-J (same candidate list, different decision model); B-vs-C is the interface effect; resource must be judged per delivered success, with recovery and completion verification separating first-decision quality from final outcome.

## 2. Purpose / constraints / non-goals

**Framing (pre-registered).** v2 is a *stress test on Jev 1.13's documented weak spots* plus a neutral anchor, with a paired comparison against a named control. It is **not** an estimate of the paper's effect sizes, and because the stressors are chosen from Jev's own jaggedness list, a control advantage on stressor families must be read as "Jev is weaker where its vendor says it is weaker", not as a general C-vs-J verdict. The neutral `anchor` family (explicit, v1-style) is reported separately for exactly this reason.

**Purpose.** On a fixture hard enough that first-decision errors really occur, measure with real Jev and a separately named LLM control, under one shared candidate interface: (a) decision quality and speed, (b) whether first-decision differences survive recovery and completion verification, (c) cost and time per delivered success. Decision -> attempt -> recovery/completion -> delivered-success levels stay separate.

**Constraints.** v1 frozen, never overwritten. API keys local-only, never in GitHub (repo or Actions secrets); only sanitized evidence is committed; CI verifies integrity only. Model revisions pinned (`jev-1.13.0`; control model pinned by exact ID). No test-set tuning after the first test run. Failures, invalid responses and nulls are kept. Hard spend cap enforced in the runner.

**Non-goals.** Not an ALFWorld/AndroidWorld reproduction; no claim about the paper's effect sizes; no B arm (free-form LLM without candidate interface) in v2; no auxiliary-reasoning or reflection overhead (the T3A/FastAgent mechanism) - that is a v3 topic; no prompt optimisation for Jev; no production claims.

## 3. Options considered

| Option | What | Pros | Cons |
|---|---|---|---|
| A | Harder hand-written fixture, Jev only | cheap, fast | no control, so the paper's C-vs-J contrast stays untested; hand-written cases invite tuning |
| **B (recommended)** | Procedurally generated stressor fixture, Jev vs named LLM control, pilot/test split, paired analysis | tests the central contrast with real Jev; generated instances give n and unseen test seeds; harness reused later | needs a second provider key and a pinned control model; more code |
| C | Go straight to ALFWorld with Jev | the paper's real environment | heavy setup (TextWorld/ALFWorld data, long runs), high risk of an uninformative ceiling again, no de-risked harness |

**Recommendation: B**, because it is the cheapest design that actually exercises the paper's main contrast (decision-model effect under a shared interface) with real Jev, and its arm/selector/metric harness carries over to option C unchanged. A alone would repeat v1's weakness; C first would spend the heavy effort before knowing the harness can discriminate.

## 4. Data model and trust boundaries

- **Selector interface** (already in v1): `choose(state_text, instructions, criteria, oracle=None)`. The oracle context exists only for non-model references and is never serialised into any prompt (tested by inspecting server-side requests).
- **Arms:** `jev` (`jev-1.13.0`, Choice question as in v1); `llm_control` (`claude-haiku-5-5`, identical state text and candidate list in the same order, enum-constrained forced tool call so a choice is always parseable; sampling parameters omitted because `claude-haiku-5-5` rejects non-default values, so the control is **stochastic** and its run-to-run variability is reported, not hidden; named "LLM candidate-interface control", **never** "Jev"); non-model references (`oracle_on_path`, `first_candidate`, `declare_done_immediately`) for floor/ceiling context.
- **Fixture generator:** deterministic, seeded; template families x instance seeds; truth always from the BFS oracle over the state machine (external deterministic truth, no model-labelled truth). Generator source and parameters are hashed.
- **Trust boundary:** keys only in the local process environment; the runner refuses output containing key material; evidence is allowlist-sanitized; CI sees only evidence + fixture.

## 5. Families, order conditions and episode types

| Family | Mechanism | Link |
|---|---|---|
| anchor | explicit v1-style task, prerequisites stated in descriptions | neutral control (not a stressor) |
| indirection | prerequisite chain 2-3 hops deep; state shows only the immediate fact | Jev: indirection |
| distractors | 24-32 irrelevant state fields + log lines named exactly like relevant ones, plus plausible irrelevant actions | Jev: large irrelevant state |
| order_decoy | near-identical commit targets (draft / preview / production) differing only in the detail the goal names; no verdict text | literal reading, option order |
| literal | negations and scoping words ("does NOT delete the original") with surface-similar labels | Jev: literal reading |
| numeric | prerequisite hinges on a threshold (>= 7 days) shown only as a number; both sides of the threshold present | Jev: numbers |
| injected | log line instructs a wrong action; truth unchanged | Jev: adversarial content |
| premature | multi-part goal where an intermediate state displays `status: complete` | paper C5 |
| irreversible | tempting reset destroys data and clears undo history; unrecoverable by design | paper C5 (negative control for recovery) |

**Order conditions** (replaces the earlier "Latin square" wording, which did not match the code): every instance is presented under three fixed candidate orders - 0 = trap first, 1 = step-0 truth first, 2 = neither first - with the rest in base order and `abstain` always last. Candidate positions of the truth and the trap at step 0 (`truth_pos`, `trap_pos`) are recorded in every row, so first-option bias is measured, not assumed away.

**Episode types.**
- `natural`: the arm chooses every action. Gives decision accuracy, natural deviation, final success, cost/time per delivered success.
- `forced_trap` (**primary endpoint for C5, recovery**): the harness forces step 0 to the instance's trap action (no selector call), so every arm continues from the *identical* error state with equal recovery opportunity regardless of its first-decision accuracy. This is the direct analogue of the paper's Reflexion finding (Jev better on first trials, worse on recovery). `irreversible` is a negative control (must fail for everyone) and is excluded from the recovery endpoint.

Sizing: 9 families x 12 test instances = 108 instances; x 3 orders = 324 natural episodes per arm; forced-trap probes on the 8 recoverable families x 12 x 3 = 288 per arm (the irreversible negative control adds 36). Pilot: 9 x 4 = 36 instances with disjoint seeds.

## 6. Pilot, freeze, pre-registration

1. **Pilot** (own seeds; may be inspected and used to calibrate): verifies both arm adapters work and checks a **pre-registered difficulty window, defined exactly as**: for each arm separately, the fraction of pilot *natural* episodes (pooled over stressor families and all three orders, `anchor` excluded) with `initial_choice_correct == False` must lie in **[10%, 60%]**. Calibrating on both arms (not on Jev alone) avoids tuning difficulty to one arm's weakness. If either arm is outside, adjust generator difficulty parameters (documented in the pilot evidence), regenerate **test seeds that have never been run**, and repeat the pilot. Pilot evidence is committed and kept regardless.
2. **Freeze:** commit the generator, parameters, test seeds, prompts, arm configs, pricing, spend cap, statistics plan and decision rules; pin their sha256 in the runner. Any later change => `v3`.
3. **Test run:** each arm runs the test set once. No re-runs on bad outcomes; infrastructure failures stay in the denominator as failures flagged `infra`.

**Arm separability (security/ops).** Each arm runs as its **own process** with only its own key in the environment and produces its **own sanitized evidence file** (leak-checked against that arm's key). Rows carry `arm` and arm-neutral field names (`cost_usd`, `decision_latency_total_s`, `n_selector_calls`; no `jev_` fields for the control). A deterministic analysis script reads both files and produces the paired contrasts; CI verifies each file and the analysis. Both arms are run with `SSL_CERT_FILE=/etc/ssl/cert.pem` on this Mac.

**Control adapter (step 2, implemented offline).** Pinned from current Anthropic docs via the `claude-api` skill (2026-10-14): `claude-haiku-5-5` accepts only default sampling (`temperature` must be 1, `top_p` 0.99; others 400), so none are sent; a forced `tool_choice` on a `strict` enum-valued tool is accepted and skips thinking, which makes the control a fast selector comparable to Jev's role; `output_config.effort` is pinned to `low`; usage comes from `response.usage`, the request id from the SDK's `_request_id`; price is $0.10 / $0.50 per MTok for prompts up to 100K tokens (newer tokenizer, about 30% more tokens than Haiku 4.5); SDK retries are disabled (`max_retries=0`) so backoff is logged separately from latency; there is no server-side refusal fallback for this model (a refusal is recorded as an invalid response). The candidate list is rendered into the control prompt in the same order Jev receives. Code: `experiments/jev_v2_arms.py` (arms, spend guard), tested against fake clients only.

### Pilot 1 outcome (2026-10-14; evidence kept, never overwritten)

Files: `evidence/jev_v2_pilot_{jev,control}.result.json`, `evidence/jev_v2_pilot_analysis.json` (CI-verified). 36 pilot instances x 3 orders x {natural, forced_trap} = 216 episodes per arm, no infrastructure failures, spend $0.025 (Jev) + $0.114 (control).

| | Jev (`jev-1.13.0`) | Control (`claude-haiku-5-5`) |
|---|---|---|
| Difficulty window (initial error, stress families) | **30.2% - inside [10%, 60%]** | **6.3% - outside (below 10%)** |
| Initial correct, stress natural | 69.8% | 93.8% |
| Final success, stress natural | 88.5% | 100% |
| Forced-trap recovery (primary C5, recoverable) | 83.3% | 99.0% |
| Decision latency / call | 0.19 s | 1.58 s |
| Cost per delivered success (natural) | $1.2e-04 | $5.0e-04 |

Pre-registered rule consequence: the control is outside the window, so the rule requires adjusting generator difficulty, regenerating **unseen** test seeds and repeating the pilot. Pilot-only observations (descriptive, n=36 instances, stressors chosen from Jev's weak-spot list, difficulty not yet calibrated for the control): Jev's errors concentrate in `indirection` (50% initial error, 17% forced-trap recovery), `injected` (50%) and `numeric` (42%); Jev abstains on 14/108 natural first decisions (control 0/108), which the window definition counts as an error but which is reported separately; `anchor` is 100% for both arms; order effects are small (Jev initial error 31% / 28% / 22% for trap-first / truth-first / neither). Design defect found: in `premature`, Jev (12/12) and Haiku (42%) fail by attaching the receipt *before* submitting, so the family exercises a prerequisite violation, not premature completion (premature completions: 0 for both arms) - the family needs redesign so that the "looks complete" state is reachable without a prerequisite error.

Reading guard: these pilot numbers are for calibration and harness validation; they are not the test result and must not be quoted as the C-vs-J finding.

### Pilot 2 outcome (generator g2, calibration iteration 1; unseen seeds 1100-1103; evidence kept)

Files: `evidence/jev_v2_pilot2_{jev,control}.result.json`, `evidence/jev_v2_pilot2_analysis.json` (CI-verified). Spend $0.030 (Jev) + $0.132 (control); no infrastructure failures or invalid responses.

| | Jev | Control |
|---|---|---|
| Difficulty window (initial error, stress) | **22.9% - inside** | **2.1% - outside (pilot 1: 6.3%)** |
| Final success, stress natural | 80.2% | 97.9% |
| Forced-trap recovery (primary C5) | 79.2% | 93.8% |
| Decision latency / call | 0.20 s | 1.53 s |

The rule's remedy (harder generator) made the control *easier*, not harder: its initial errors fell from 6.3% to 2.1% while Jev stayed inside the window. Per-family: Jev floors on `injected` (100% initial error, 8% success) and is at 67% on `numeric`; the redesigned `premature` family does not discriminate (0 premature completions for either arm); control's remaining weaknesses are small (indirection 83% final success, literal forced recovery 67%). Reaching >=10% control error would require stressors that push Jev toward the floor, defeating the "both arms non-degenerate" purpose of the window. Pilot-only numbers; not the test result.

## 7. Metrics and decision rules (pre-registered)

Per arm and per stressor family:
- Decision level: valid-choice rate, exact accuracy, abstain rate, order sensitivity (answer changes across permutations), latency mean/p50/p95, token cost.
- Attempt level: initial_choice_correct, prerequisite_valid.
- Recovery/completion: deviation rate, recovery attempted/success among deviations, premature completion, verification errors.
- Delivered success: success rate, cost per delivered success, time per delivered success (failures stay in the numerator), `initial_correct_but_final_failed`, `initial_wrong_but_final_success`.

Paired contrasts (control - Jev) on identical instances and permutations, with **instance-cluster bootstrap 95% intervals** (permutations of one instance are not independent) and McNemar for paired binary outcomes. Descriptive only: no multiplicity-adjusted significance claim, no causal claim.

Transfer classification reuses the audit's semantics: decision delta, task delta, delivery delta -> `TRANSFERRED` / `DELIVERY_PARADOX` / `NO_LOCAL_SAVING`. `OVERHEAD_ABSORPTION` cannot occur in v2 (no auxiliary overhead by design) and is reported as "not testable here".

Interpretation guards: a Jev decision advantage never reads as an agent advantage unless delivered-success metrics agree; the floor/ceiling outcomes (both arms near 0 or 100%) are reported as non-discriminating, not as support.

## 8. Failure modes (fail-closed unless stated)

| Failure | Behaviour |
|---|---|
| Identity step fails (bad key, TLS, network) | abort, no evidence (v1 behaviour); known macOS fix `SSL_CERT_FILE=/etc/ssl/cert.pem` |
| Mid-run API outage / rate-limit exhaustion | episode recorded as infra failure (kept, in denominator); run marked INCOMPLETE if >2% infra; no silent retry beyond the frozen policy |
| Spend cap reached | stop, evidence marked INCOMPLETE, partial rows kept |
| Control returns unparseable output | counted invalid, kept (fail-open for accounting, fail-closed for state: no transition) |
| Key material in output | refuse to write (existing guard) |
| Order bias confound | counterbalanced permutations; order sensitivity reported separately |
| Ceiling/floor again | pre-registered difficulty window; reported as non-discriminating if it recurs |
| Contamination of test by pilot | disjoint seed ranges, asserted in tests |

## 9. Verification plan (how "done" is shown)

- Offline tests (no API): generator determinism and hash pin; oracle reaches 100% on every generated instance; each family produces its intended failure mode under scripted selectors; permutations are a valid Latin square; paired-bootstrap code on known data; request inspection proves no oracle leakage.
- Pilot evidence committed; difficulty-window check recorded.
- Live test evidence (sanitized) committed unmodified; extended `verify_jev_live_evidence.py` recomputes aggregates, contrasts and classifications from rows in CI.
- CI green; `status.yaml`/`report.md`/`HANDOFF.md` updated; `reproduction_status` stays `PARTIAL`.

## 10. Steps (each independently deployable and revertible)

1. v2 generator + stressor families + offline tests (no keys, no API).
2. Arm adapters: Jev (reuse v1 client) + control adapter + spend cap + paired statistics + extended verifier, offline-tested against fake servers.
3. Pilot run (local), difficulty-window check, calibration, pilot evidence committed.
4. Freeze + pre-registration commit (hashes pinned).
5. Test run (local, once per arm), sanitized evidence committed, CI verification, docs/status update.

## 11. Decisions (2026-10-14, user)

1. **Control = `claude-haiku-5-5` via the Anthropic API directly** (user supplies `ANTHROPIC_API_KEY` in the local environment only; key validity and model availability were checked on 2026-10-14 via the model list, no spend). Labelled "LLM candidate-interface control (claude-haiku-5-5)", never as Jev. The `claude -p` headless route was considered and rejected for the primary control (no temperature control, CLI startup in latency, nominal cost); speed/cost are therefore comparable at API level.
2. **Spend cap: US$5** total for pilot + test across both arms (runner-enforced).
3. B arm and auxiliary-overhead mechanisms deferred to v3 (assumed; not objected to).

Implementation note: v1 is frozen, so v2 gets its own core (`jev_v2_core.py`, a superset of the v1 machine adding hidden state keys, custom prerequisite messages, irreversible actions, log/distractor rendering and candidate rotation) and a seeded generator (`jev_v2_generator.py`). Control API details (structured output, temperature, parameters of the pinned model) must be checked against current Anthropic docs before step 2.

## 12. Test outcome (frozen g2, seeds 3000-3011, run once per arm, 2026-10-14)

Files (sanitized, committed unmodified; CI-verified): `evidence/jev_v2_test_jev.result.json` (sha256 `dcbc276bf8533cab3cfeca60ad1ec397aeedbcea8e0508a9caf4429be4c696ad`), `evidence/jev_v2_test_control.result.json` (`39c8650b4e8d83b8dd7957d6e555254d4152aea2d241c0483371f57c9b57a96d`), `evidence/jev_v2_test_analysis.json` (`19e9cf0385acfee06a977b9ee05fce9a54f9a15a6c8ccb980bfa79ec9dddf23c`). Freeze pin `f76ba2b6...` matched; both arms COMPLETED, 648/648 rows, 0 infrastructure failures, 0 invalid responses. Spend US$0.087 (Jev) + US$0.380 (control) of the US$5 cap. Keys were never written to the repo; evidence was leak-checked against both keys. No re-run, no post-hoc changes.

| Pre-registered endpoint (control - Jev, instance-cluster bootstrap 95% CI, exact McNemar) | Jev | Control | Diff | 95% CI | discordant (control-only / Jev-only), p |
|---|---|---|---|---|---|
| **Primary: forced-trap recovery, recoverable families (n=288)** | 87.2% | 97.2% | +10.1 pt | [3.5, 17.4] | 35 / 6, p=4.9e-06 |
| Initial choice correct, stress natural (n=288) | 79.9% | 95.5% | +15.6 pt | [8.7, 22.9] | 52 / 7, p=1.4e-09 |
| Final success, stress natural (n=288) | 84.0% | 98.6% | +14.6 pt | [7.6, 21.9] | 45 / 3, p=1.3e-10 |
| `anchor` natural initial / final (n=36) | 100% / 100% | 100% / 100% | 0 | - | non-discriminating (ceiling) |
| `irreversible` forced-trap (negative control, n=36) | 0% | 0% | 0 | - | behaved as designed |
| Decision latency / call (natural) | 0.19 s | 1.52 s | | [1.29, 1.36] on the diff | reference only (different providers) |
| Time per delivered success (natural) | 1.10 s | 6.34 s | | | reference only |
| Cost per delivered success (natural; Jev cost = tokens x assumed $0.042/Mtok) | $1.5e-04 | $5.6e-04 | | | reference only |

Transfer classification (Jev vs control, delivered-success based): decision latency -87%, task latency -85%, delivered time -83% => class `TRANSFERRED` for time. Because success rates differ (84% vs 98.6% natural stress), this speed result must be read together with the success gap, as pre-registered rule 1 requires.

Where the gap comes from (derived from `by_family`): it is concentrated. `injected` (instruction embedded in a log/distractor): Jev initial correct 0/36, final success 13.9% natural / 19.4% forced, control 97.2% on both. `numeric`: Jev initial correct 21/36 and natural final success 58.3% (forced-trap recovery 100%: once pushed off the trap Jev recovers). `distractors` initial 29/36 vs 32/36 but final success 100% for both. Excluding `injected` the primary endpoint is 96.8% (Jev) vs 97.2% (control), i.e. no meaningful difference. `indirection` went the other way (Jev 100%, control 91.7% final success). `literal` forced-trap recovery 77.8% vs 88.9%. `order_decoy` and `premature` non-discriminating (100% both; 0 premature completions in either arm, as in the pilots). Order effect (initial correct, control - Jev): trap-first +25.0 pt, truth-first +14.6 pt, neither +7.3 pt (CI includes 0). Jev abstained on 23/324 natural first decisions (control 1/324).

Reading (binding, per the pre-registration): this is a stress test on Jev 1.13's documented weak spots, not an ALFWorld/AndroidWorld reproduction and not an estimate of the paper's effect sizes. Findings: (1) on this fixture the LLM candidate-interface control (claude-haiku-5-5) is at or above Jev on delivered success, so Jev's decision speed advantage does **not** become an agent advantage here (the paper's own "faster decisions do not make better agents" caution is consistent with this, but this is not a test of the paper's claim); (2) the deficit is largely one stressor family (`injected`) plus `numeric` initial choice; (3) recovery from a forced wrong first action is good for Jev outside `injected` and `literal`; (4) the control stayed outside the pre-registered difficulty window (initial error 4.5% on stress natural), so natural-episode comparisons mostly measure Jev errors, as disclosed before the run; (5) one run per arm, stochastic control, descriptive statistics only, no multiplicity adjustment. B arm and auxiliary-overhead mechanisms (T3A/FastAgent-type) remain untested (v3).
