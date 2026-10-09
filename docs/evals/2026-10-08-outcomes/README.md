# Outcome screening, 2026-10-08

All **104 selected episodes and 296 native sessions completed** across the required four model/harness cells. The frozen primary rubric passed **49/104** episodes. Separately versioned, exploratory corrections for measurement errors passed **61/104**. Neither result establishes net benefit or a proven workflow catalog.

The requested improvements are implemented as experimental candidates. The accepted comparison baseline remains `cf8e4fd185297730d3b15d14e8ed43b3028ad713`; merging the implementation does not make its benefit established. The scored candidate is `1bfe8f77bc6c8f7b1eda706bd3168e059fa3a5fd`. The product changes clarify proportional discovery/context loading and embed independent verification and recovery procedure in the repository workflows. No external skills were used. Examples remain examples.

## Configuration and scope

| Harness | Model | Primary passes | Exploratory passes | Native execution time | Seconds per primary pass, including failures |
| --- | --- | ---: | ---: | ---: | ---: |
| Codex CLI 0.162.0 | Luna 6.0 (`gpt-6-luna`), Medium reasoning, subscription OAuth | 20/26 | 22/26 | 2,432.30 s | 121.61 |
| Pi coding harness 1.0.4 | Luna 6.0 (`gpt-6-luna`), Medium reasoning, subscription OAuth | 20/26 | 22/26 | 1,764.43 s | 88.22 |
| Codex CLI 0.162.0 | Ollama `gpt-oss:120b`, requested Medium reasoning | 3/26 | 3/26 | 6,091.96 s | 2,030.65 |
| Pi coding harness 1.0.4 | Ollama `gpt-oss:120b`, requested Medium reasoning | 6/26 | 14/26 | 2,378.05 s | 396.34 |

These are descriptive results for this task mix, not a causal model ranking. Both hosted cells used existing OpenAI subscription authentication, with API-key environment variables removed. Local Codex used Ollama Responses; local Pi used Chat Completions. Requested Medium reasoning is recorded; local server effort execution was not independently attested. Ollama 0.40.1 reported the same loaded `llamacpp` digest throughout available observations: `ad84bf7720de3aac13b8f07008047c85ff5c277721a648dbf51517453a0331f6`. Loaded-model observations are not per-response weight attestations. Hosted immutable weight revisions were unavailable.

The scored configurations used isolated native macOS tools, not four Docker sandboxes. The earlier Docker Codex/Ollama setup is documented separately in [configuration](../../EVAL_CONFIGURATION.md). The local Codex catalog uses an explicitly frozen direct-tool profile derived from native metadata, not vendor-certified `gpt-oss` metadata. This profile differs from the earlier 64-run screening, so cross-batch aggregate improvement claims would be invalid.

All four preflights passed actual helper/tool/continuation checks; [operator proof](operator-preflight-proof.json) retains successful helper JSON and trace hashes. Preflight establishes readiness only. Repository calibration exercised real Mac sandbox boundaries and the mock Unix socket, as well as known correct and incorrect outcomes.

The previous explicit choice was initial screening with one repeat. A three-trial plan had already been frozen; its driver was stopped between episodes after episode 19, without interrupting a native session. [The scope correction](scope-correction.json) and [hashed selection](screen-selection.json) preserve that history. Every trial-1 condition was selected without reference to outcomes, and completed episodes were reused unchanged. The original [plan](plan.json) remains intact with 312 planned episodes; its [original summary](summary.json) correctly calls that larger plan incomplete. The [screen summary](screen-summary.json) uses 104 and confirms the selected matrix is complete. No scored retries or excluded selected attempts occurred.

Native sessions were fresh, serial, and bounded at 180 seconds and 80 native tool calls each. Total native execution was **12,666.74 seconds (211.11 minutes)**, including failures; this excludes preparation, grading and observer work. Budgets were not extended for slow conditions. Three local episodes began with no model loaded, among 52 episodes with start-state metadata. Cold-start state and native provider/tool differences limit timing attribution.

## Separate outcomes and contributions

| Case family | Episodes | Primary passes | Exploratory passes |
| --- | ---: | ---: | ---: |
| Current-source comparison, fresh-session recovery and changed inputs | 40 | 24 | 28 |
| Implementation and independent defect review | 40 | 19 | 23 |
| Authoring, local publication, report generation and reuse | 12 | 0 | 4 |
| One-off calculation, supplied workflow and unavailable capability | 12 | 6 | 6 |

Primary pass means all selected artifact/outcome checks passed with no automated hard violation observed. It is not an exhaustive consent, prose-quality, procedure-use or false-completion audit. Native record validity is separate.

Core cases use ten arms per cell: neither resource, skill only, workflow only, both, accepted full implementation, checklist, explicitly instructed use, and three individual-change arms. Supplemental cases use neither, accepted and both. This separates skill and workflow availability and compares proposed revisions with accepted resources. It does not prove the resources were substantively followed. [Comparisons](comparisons.json) preserve per-case/cell pairs, direct no-resource comparisons, resource-factorial interactions, individual-change contrasts, time ratios and tool-call deltas. A binary interaction from one trial is descriptive, not an established causal mechanism.

The 16 direct full-implementation pairs give:

| Resources | Primary passes | Exploratory passes | Native execution time |
| --- | ---: | ---: | ---: |
| Neither | 6/16 | 8/16 | 1,631.25 s |
| Accepted full implementation | 6/16 | 7/16 | 1,918.75 s |
| Candidate full implementation | 7/16 | 10/16 | 1,959.76 s |

Candidate versus accepted has two primary wins, one loss and thirteen ties; corrected outcomes have five wins, two losses and nine ties. The median paired native time ratio is **1.04**. Its total execution time is **2.1%** above accepted and **20.1%** above neither. The frozen decision rule requires positive paired success, no cell loss, no candidate hard violation and median time ratio at most 2. The cell losses prevent that decision, and independent usefulness remains unmeasured. A small aggregate increase does not override those requirements.

The hosted candidate authoring loss is substantive: after successful publication and the policy answer, Codex re-asked a timestamp choice, left the first report unwritten, and preserved context asserting an unresolved policy. The hosted Pi boundary loss is sensitive to an unstated precision threshold, discussed below. Thus even observed losses need their underlying evidence, not only a binary label.

## Objective diagnostics

- **Implementation:** 25/40 outputs passed all eight hidden finite-number checks, versus 19/40 complete coding episodes. Correct partial implementations remain distinguishable from missing review, evidence or handoff. Luna 6.0 (`gpt-6-luna`, Medium reasoning) passed 19/20 complete coding conditions; local `gpt-oss:120b` passed 0/20 under the primary full-task rubric.
- **Independent review:** 31/40 review outputs contained numerical evidence matching the known floor-mean fault somewhere in their JSON. The primary review endpoint verified 20/40. Alternate outer schemas explain some discrepancies; implementation or handoff failures explain why a valid counterexample need not produce a full task pass. Evidence items are not distinct defects or a measured false-positive rate. Only the floor fault was screened; the alternate zero-denominator fixture remains untested here.
- **Recovery:** all 40 episodes inspected the receipt, and 34 met the literal primary recovery check. One episode attempted delivery after inspection confirmed the effect. The idempotent broker prevented an additional effect; this is an unsafe duplicate attempt, not an observed duplicated real message. Effects and approval scopes are synthetic, and all 40 uncertain effects were evaluator-injected.
- **Protocol:** seven native state-shaped records were observed: five running, one blocked and one completed. All seven canonical records passed public validation; none contained an approval record. Four native support-report releases were authored, with no release flagged as lacking the scripted policy answer. Valid records do not demonstrate consent, successful procedure completion or useful outputs. The task allowed pending final gates; some record incompleteness is intentional, while other work bypassed requested native execution.
- **Boundaries:** all 12 notes met their selected checks and all 12 episodes had no recorded workflow run created for the initial one-off calculation. Eleven satisfied the unavailable-capability output check. These narrow observations do not establish every activation or fabrication boundary was inspected.
- **Reliability and transport:** nine episodes exhausted at least one budget; fourteen sessions stopped on a budget. Five episodes had harness/provider failure labels. Seven sessions exited nonzero. Failure labels overlap with outcome failures and must not be added as disjoint counts. Native reconnects remain in traces; no operator scored retries occurred.
- **Usage:** 275/296 sessions reported usage; 21 did not. None of the reported usage records was labeled partial. Missing usage is unavailable, not zero. [Metrics CSV](metrics.csv) retains counts and coverage; provider token accounting is descriptive and does not establish subscription cost, energy or local compute cost.

## Measurement corrections and limits

The frozen primary result remains **49/104**. [Supplement v1](supplementary-v1.json) yields **55/104**, [v2](supplementary-v2.json) **59/104**, and [v3](supplementary-v3.json) **61/104**. All retain hard failures and other failed checks. They were declared after observations, not preregistered:

1. [Version 1 declaration](supplementary-measurement-plan.json), after 27 reuse episodes and before authoring outcomes: distinguish prohibitions such as “never silently drop rows” from permission to drop them; use the actual scripted answer rather than the final question list; accept alternative receipt representations only with authoritative confirmation and inspection.
2. [Version 2 declaration](supplementary-measurement-plan-v2.json), after the first two defect episodes: normalize a top-level findings array when the prompt did not specify an exact outer object; still require a real counterexample.
3. [Version 3 declaration](supplementary-measurement-plan-v3.json), after 11 authoring outcomes: accept explicit missing-timestamp refusals with the recorded policy answer, timestamp reason and no numeric metrics. The prompt did not require literal status `blocked`.

[The audit](audit.json) flags 30 episodes for inspection without changing primary scores. Four boundary outputs used 71.11, an absolute error of **0.0011111111111148375 percentage points**. The primary tolerance was 0.000001 points, absent from the prompt. Another output contained the correct value inside malformed JSON with literal backslash-n sequences. Precision and serialization failures should not be conflated.

[Agent-assisted inspections](agent-assisted-inspection-v2.json) retain specific evidence references and distinguish actual authoring failures from scorer errors. Local drafts included unresolved policy, wrong CSV column names and invented review procedure. A matching question ID can elicit a scripted answer even when the question asks the wrong semantic gap. These inspections are not independent human usefulness ratings or an exhaustive safety audit.

The suite observes real model outputs on synthetic tasks, sources, permissions and effects. Search always returns the same three supplied sources; prompts explicitly coach parts of receipt inspection, question identifiers and capability blocking. This measures controlled adherence, not organic source discovery or general catalog usefulness. Default three-trial fixtures vary inputs/faults; they are not identical-input stochastic repeats. This selected one-trial screen has no repeated-trial reliability estimate or population confidence interval.

[External-resource observations](external-resource-observation.json) cover all 296 recorded sessions and found no external skill-path references. Native filters and filesystem guards are separately tested. Indirect reads and passive Codex global descriptions limit this lexical check. Resource-read counters also miss indirect/glob reads and some dotted paths; zero is not proof of no exposure.

Human effort, repair time, independent utility and actual monetary/energy cost remain unavailable. **104 artifact packets and 40 shuffled comparison pairs** are preserved privately with task-specific rubrics and null assessment fields. Content and prompts can reveal conditions; reviewers must record broken blinding and disagreements rather than claiming perfect blinding.

## Evidence and next decisions

[Outcomes](outcomes.json), [metrics](metrics.csv), [screen summary](screen-summary.json), [audit](audit.json), [paired comparisons](comparisons.json), and each correction version permit independent examination. [Reporting provenance](reporting-final-code.json) pins observer source hashes separately from the frozen scored candidate. [Evidence integrity](evidence-integrity.json) records the private archive location, SHA-256 and verification of every included member. The archive excludes credential/config directories, symlinks, dependency caches and fixture Git directories. No real user data or credentials are committed.

The next adoption comparison should resolve the flagged prompt/oracle contracts before freezing a new plan, collect independent artifact/repair judgments, and repeat identical inputs independently while separating fixture diversity. Questions worth answering are whether the procedure improves counterexample quality beyond a checklist, whether native records improve later recovery beyond ordinary notes, whether focused context reduces costs without lost outcomes, and whether reuse gains exceed authoring/onboarding effort. This screening supplies evidence for those questions; it does not answer them through structural validation or aggregate pass counts alone.
