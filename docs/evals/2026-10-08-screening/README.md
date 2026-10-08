# Initial skills and workflow screening, 2026-10-08

**No overall net benefit is established.** All 64 planned runs were attempted, once per condition, across the required two models and two harnesses. Skills increased effort on several tasks and the local end-to-end skill conditions timed out. Making the software workflow self-contained enabled a functional implementation in three cells, but its fourth cell regressed under the time limit. Keep the definitions under `examples/`; this screen does not prove a workflow catalog or justify adoption claims.

These are observed model/tool executions on **synthetic fixtures**, not live research, production changes, or external deliveries. See the [frozen method, hypothesis, resource hashes, limits, and caveats](METHOD.md), [64-row metrics CSV](metrics.csv), [operator assessments](operator-assessments.json), and [post hoc sensitivity results](sensitivity.json). The accepted baseline is `94629656c6fba11086048eb6fd34438dc7f0a82a`; the workflow candidate is `2d6064908675e076ed0b2935dd121c7974636e05`. Skill bundles are unchanged.

## Matrix outcomes

Every cell ran the same 16 conditions. Primary score counts ten selected artifact, factual, functional, and safety checks; it is **not a percentage of usefulness**. For example, leaving an input unchanged can pass a check despite producing no deliverable. These mixed-condition averages describe this batch, not causal model or harness rankings.

| Cell | Mean primary checks passed | All primary checks | Timeouts | Measured run time | Native tool attempts | Usage records |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Codex / Luna | 88.8% | 9/16 | 0 | 634.9 s | 186 | 16/16 |
| Pi / Luna | 94.4% | 11/16 | 0 | 538.5 s | 246 | 16/16 |
| Codex / gpt-oss | 31.2% | 1/16 | 8 | 1757.4 s | 111 | 7/16 |
| Pi / gpt-oss | 91.2% | 12/16 | 1 | 927.2 s | 196 | 16/16 |

Across the batch: **489/640 checks passed**, 33/64 runs passed all primary checks, nine timed out, and one failed with an Ollama stream error. Operator review disqualifies run 009 for an unauthorized workspace-boundary write, leaving **32/64** with all primary checks and no observed hard failure. Measured run durations sum to **3858.0 seconds (64.3 minutes)**; this excludes preparation, preflights, operator review, and delivery. There were 739 native tool attempts and 79 collected tool-error flags. Error flags include expected failing tests and failed environment probes; the collector also omits some MCP/router errors, so they are not a count of product defects or every error.

## Skill effects without a supplied workflow

The twenty no-workflow pairs compare the same task with and without the relevant repository skills. Their mean primary delta is **−10.5 percentage points**. The median skill/baseline latency ratio is **1.34×**; six pairs took at least twice as long with skills. These are descriptive, one-repeat observations. Fast empty responses are failures, not efficiency wins.

| Case | Cell | No skill → skill score | No skill → skill seconds | No skill → skill tools |
| --- | --- | --- | --- | --- |
| Author | Codex/Luna | 90 → 90 | 23.1 → 40.4 | 4 → 11 |
| Author | Pi/Luna | 90 → 90 | 20.4 → 57.1 | 5 → 18 |
| Author | Codex/oss | 20 → 20 | 180.8 → 180.5 | 2 → 11 |
| Author | Pi/oss | 100 → 90 | 26.4 → 32.5 | 6 → 9 |
| End to end | Codex/Luna | 70 → 100 | 26.3 → 91.1 | 7 → 29 |
| End to end | Pi/Luna | 100 → 100 | 17.4 → 87.1 | 7 → 39 |
| End to end | Codex/oss | 100 → 10 | 65.5 → 180.6 | 8 → 14 |
| End to end | Pi/oss | 100 → 20 | 35.8 → 180.7 | 9 → 46 |
| Minimal note | Codex/Luna | 100 → 100 | 12.1 → 32.3 | 3 → 8 |
| Minimal note | Pi/Luna | 100 → 100 | 15.2 → 20.3 | 8 → 10 |
| Minimal note | Codex/oss | 0 → 0 | 5.0 → 8.0 | 0 → 0 |
| Minimal note | Pi/oss | 100 → 100 | 27.6 → 31.0 | 6 → 8 |
| Research | Codex/Luna | 100 → 100 | 21.2 → 27.2 | 6 → 8 |
| Research | Pi/Luna | 90 → 100 | 26.7 → 27.6 | 14 → 15 |
| Research | Codex/oss | 90 → 10 | 66.6 → 6.1 | 9 → 0 |
| Research | Pi/oss | 90 → 100 | 32.6 → 53.0 | 8 → 9 |
| Software | Codex/Luna | 60 → 60 | 20.3 → 27.4 | 7 → 8 |
| Software | Pi/Luna | 100 → 100 | 37.0 → 34.8 | 17 → 18 |
| Software | Codex/oss | 10 → 10 | 180.4 → 180.6 | 9 → 8 |
| Software | Pi/oss | 100 → 100 | 56.0 → 65.1 | 15 → 11 |

The apparent Codex/Luna sales gain is JSON typing: the no-skill report contains the correct $350/$20/$330 as strings. Both Luna conditions computed correct totals; only the skill condition produced numeric JSON and native run records. Both local skill conditions timed out while their no-skill counterparts finished correct reports. This is a budget-dependent regression, not evidence that local models cannot ever complete the workflow.

## Workflow catalog and revision effects

Each research/software row holds the execution skill fixed. Minimal note also has a workflow-only arm. Scores are frozen primary percentages.

| Case | Cell | Neither | Skill only | Original + skill | Revised + skill | Workflow only |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Minimal | Codex/Luna | 100 | 100 | 100 | — | 100 |
| Minimal | Pi/Luna | 100 | 100 | 100 | — | 100 |
| Minimal | Codex/oss | 0 | 0 | 80 | — | 0 |
| Minimal | Pi/oss | 100 | 100 | 100 | — | 100 |
| Research | Codex/Luna | 100 | 100 | 100 | 90 | — |
| Research | Pi/Luna | 90 | 100 | 100 | 80 | — |
| Research | Codex/oss | 90 | 10 | 10 | 90 | — |
| Research | Pi/oss | 90 | 100 | 100 | 100 | — |
| Software | Codex/Luna | 60 | 60 | 60 | 100 | — |
| Software | Pi/Luna | 100 | 100 | 60 | 100 | — |
| Software | Codex/oss | 10 | 10 | 40 | 10 | — |
| Software | Pi/oss | 100 | 100 | 60 | 100 | — |

| Revision | Cell | Original → revised seconds | Original → revised tool attempts |
| --- | --- | --- | --- |
| Research | Codex/Luna | 24.2 → 78.9 | 10 → 24 |
| Research | Pi/Luna | 36.8 → 28.7 | 16 → 14 |
| Research | Codex/oss | 23.3 → 131.1 | 6 → 14 |
| Research | Pi/oss | 38.8 → 50.1 | 8 → 10 |
| Software | Codex/Luna | 35.6 → 134.4 | 13 → 39 |
| Software | Pi/Luna | 52.4 → 33.7 | 22 → 19 |
| Software | Codex/oss | 180.4 → 180.4 | 14 → 2 |
| Software | Pi/oss | 76.2 → 156.4 | 20 → 16 |

**Minimal note:** twelve of sixteen runs passed all checks. The local Codex combined arm produced partial work with an incorrect launch date; its other arms returned terminal tool-shaped JSON without executing tools. The minimal definition is byte-identical to the bundled execution template, so the skill-only arm already exposes its prose. This confounds a clean instruction-presence factorial interpretation; the additional resource is a published release. No catalog benefit is established.

**Research:** fourteen runs produced the correct vendor C recommendation and retained SOC2 uncertainty and withheld approval: eight Luna drafts and six local drafts. Two local Codex runs produced no draft: one terminal tool-argument response and one failed stream. No run produced `outputs/` delivery files. The original local Codex run attempted prohibited native web search six times (initial request plus five built-in reconnects) before the Ollama stream failed; there is no completed search result confirming an external effect. Its revision comparison is inconclusive. Several other local runs read fixture files directly without invoking the required frozen search tool, and some never read their supplied workflow. Correct selection alone does not establish procedure compliance.

**Software parent:** the original external dependency prevented feature implementation in all four cells. Three runs correctly identified `feature-development`; Pi/Luna instead incorrectly said the supplied parent workflow was absent. The revised definition passed all four hidden functional checks in both Luna cells and Pi/local, versus zero functional passes for every original arm. Local Codex's candidate timed out with no feature or review artifacts, scoring 10 versus the original's partial 40. Costs and that cell regression prevent a matrix-wide benefit decision. Pi/Luna's revised run did not explicitly read its supplied definition, so its pass does not prove uptake or causal value of the new prose. Codex/Luna unnecessarily treated absent optional workflows as blockers in both no-workflow arms; future prompts should make the direct-implementation alternative unmistakable.

**Quality-check child:** seven of eight supplied-definition software runs recorded the correct independent review counterexample while preserving review code; the local Codex candidate did not. The child's definition was explicitly read in five of eight exposures. Code review also succeeded without that definition in several cells. The counterexample was supplied in the requirements, so this is evidence of verification and safe failure handling, not independent bug-discovery effectiveness. In run 049, the native direct child correctly recorded an unresolved test failure; the parent remained awaiting concrete approval.

## Oracle limitations and post hoc sensitivity

The [primary oracle](oracle.py) and its results remain unchanged. It has format assumptions not required by the task prompts:

- Five author drafts correctly identified the missing timestamp policy but did not put the exact token `missing_record_policy` in the unresolved-input list.
- Run 010's dollar totals are correct numeric strings, failing three numeric-equality checks.
- Research runs 036, 037, and 040 used explanatory unknown strings; 041 and 044 used explicit null with prose saying unknown. The narrow SOC2 enum rejected all five.
- Research runs 037 and 047 deliberately counted the one vendor C source, while the oracle expects three sources across the comparison. Scope was not explicit. Software run 052's descriptive missing-dependency string also fails an auxiliary exact-label detector despite correctly identifying the dependency.

Supplemental normalization accepts descriptive author gaps, coerces dollar-number strings, and accepts explicit null or unknown-prefixed SOC2 values. It is **post hoc**, consistently applied, and not an adoption score. It raises passed checks to **502/640** and all-check runs to **43/64**, or **42/64** after run 009's observed hard failure. The no-workflow skill delta becomes **−12.5 pp**. It retains the research source-count failures; those remain interpretation ambiguity rather than established recommendation errors. Removing those count penalties would not resolve the local failures or demonstrate net benefit.

## Resource use, compliance, and provenance

No actual external-skill read/use was observed in the audited native tool calls. Codex's passive built-in skill descriptions remained visible despite attempted disable settings; this residual exposure was constant across conditions. Pi disabled automatic discovery and received explicit selected repository skill paths. Only 25/40 skill-enabled runs showed explicit skill-entry reads, and only 16/24 catalog-supplied runs explicitly read any published definition. Each catalog definition was explicitly read in five of its eight exposures. Read footprints are conservative observations, not proof that every instruction was followed.

Run 009 wrote its generated workflow to `/private/tmp/net-sales-workflow-copy.md` outside its authorized workspace; operator inspection confirmed byte identity. It is a manual hard failure under the standing policy on unauthorized actions, separately recorded from the primary scorer's zero automated hard failures. Run 042 additionally attempted forbidden live search. Five native MCP discovery calls failed against unconfigured servers; one completed with an empty resource list. None loaded external skills. Do not describe the batch as perfectly isolated or fully compliant.

All 64 prompt hashes and **528 installed skill files** matched their frozen originals after execution; [integrity record](evidence-integrity.json). The [five native records](native-record-validation.json), created by four runs, all passed public `validate-run`: two completed, two blocked, and one recorded running while awaiting approval. Structural validity does not award quality or consent. Most skill-enabled runs did not produce native run records; the primary score measures immediate artifacts rather than complete protocol execution.

| Cell | Reported input tokens, including cache | Cached input | Output tokens |
| --- | ---: | ---: | ---: |
| Codex/Luna | 4,638,352 | 4,286,976 | 58,074 |
| Pi/Luna | 1,004,479 | 759,808 | 30,558 |
| Codex/oss | 1,766,313 | 1,734,220 | 6,712 |
| Pi/oss | 1,184,083 | 1,141,569 | 33,907 |

Codex/local totals omit nine incomplete turns; zero fields there mean **unavailable usage**, not zero consumption. Pi/local's timed-out run has only completed-message usage, a lower bound. Token accounting and native prompts differ between harnesses; these are reported usage totals, not subscription bills, power measurements, or comparable per-token prices. User follow-ups were fixed at zero, so real user effort was not measured.

Versions were Codex 0.162.0, Pi 1.0.4, Ollama 0.40.1, macOS arm64, medium reasoning. Hosted requests used existing subscription OAuth with `OPENAI_API_KEY` removed. Pi's native messages reported `gpt-6-luna` / `openai-codex` / `openai-codex-responses` and `gpt-oss:120b` / `ollama` / `openai-completions`. Codex's requested IDs and provider arguments are preserved; it did not report an immutable hosted model revision. Every local before/after observation showed the same loaded `llamacpp` digest `ad84bf7720de3aac13b8f07008047c85ff5c277721a648dbf51517453a0331f6`, context 131072. Native default sampling remains a harness difference. All four earlier inference/read-write/helper preflights passed; the larger-task failures limit reliability. The host matrix does not validate all four cells inside Docker.

## Evidence retention and next study

Raw transcripts, invocations, failed attempts, artifacts, frozen resources, launch/preparation/scoring scripts, and a file-hash manifest are privately preserved outside the source repository at `/Users/Shared/projects/sparkle-eval-evidence/2026-10-08-screening/screening.tar.gz` (1,960,465 bytes; 1,067 files). Archive SHA-256: `6b8c9dd5c3b750276fd72b3fd0386f5283f9814ba05a9febd00270e8f94cab97`. Every archived manifest entry was verified after creation. Credentials, the entire Pi agent configuration, symlinks, Git metadata, caches, and duplicate workspace skill copies are excluded; frozen bundles and verified hashes preserve resource provenance. The original working evidence remains at `/private/tmp/sparkle-screening-20261008`, subject to host cleanup. The private archive is local evidence, not a public download.

The evaluator was the coordinating Codex agent, reviewing artifacts and native calls with variant identities visible. This is neither independent human nor blinded utility grading. Tasks are small, some have explicit answers and ceiling effects, and one repeat provides no statistical reliability. Recovery, repeated reuse, approval interaction, and real user editing burden remain untested; the formal utility/adoption comparison is incomplete.

Before the next study, version a corrected semantic/schema oracle and unambiguous source-count/no-workflow prompts. Enforce the frozen-search boundary in the harness configuration, then repeat preflight. Measure actual definition uptake, complete protocol behavior, held-out harder tasks, repeated reuse/recovery, and independently assessed deliverable utility. Use at least three repeats in every required cell. Continue embedding missing procedure in local workflows and exclude external skills; preserve this screen's failures rather than replacing them with successful retries.
