# Frozen initial screening design

This is the user-selected one-repeat screening of repository skills and the possible workflow catalog. It is not an adoption study. The plan, fixtures, prompts, limits, and primary oracle were fixed before the first scored run; exploratory configuration/isolation probes are excluded. No external skills may be used. These files are dated evidence, not the product helper or a general-purpose evaluation framework.

## Provenance

- Accepted baseline: `94629656c6fba11086048eb6fd34438dc7f0a82a`.
- Workflow candidate: `2d6064908675e076ed0b2935dd121c7974636e05` (embedded software and research procedures). The skill bundles themselves are unchanged.
- [Plan](plan.json), SHA-256 `7ac8f36809492c9920be56334d0d1f0cdf4b689024180ec81f34eaf689c4a029`, includes the exact run order, resource hashes, per-run prompt/input hashes, provider cells, and isolation limitation.
- [Synthetic cases](cases.json), SHA-256 `aecb516b3189ad4afd68f608cdd4489bcc4627e990315147e5a501906cd8a915`.
- [Primary oracle snapshot](oracle.py), SHA-256 `31c2c066ad47250c010d7a0a73b5c20367f547b443aeef9a6285323d8571f2a5`.

Machine-specific paths in the frozen plan identify the original workspaces. They are not portable setup defaults. See [the configuration guide](../../EVAL_CONFIGURATION.md) for provider authentication and dependency preparation. The raw batch directory contains the preparation and launcher scripts; no credentials belong in the evidence archive.

## Comparisons

Each arm runs once in each of the four model/harness cells. All paired arms receive identical task prompts and source fixtures.

| Case | Arms | Runs | Independent outcome |
| --- | --- | ---: | --- |
| Author | No skills; define skill | 8 | Draft a support-report procedure while preserving an unresolved timestamp policy |
| End to end | No skills; both skills | 8 | Author and execute net sales: 3 paid rows, $350 gross, $20 refunds, $330 net |
| Minimal note | Neither resource; execution skill only; original workflow only; both | 16 | Correct launch facts, unresolved security blocker, no GA approval, concise note |
| Research | Neither; execution skill only; execution + original workflow; execution + candidate workflow | 16 | Vendor C meets hard constraints; SOC2 remains unknown; no delivery before approval |
| Software | Same four arms as research | 16 | Implement finite-number summarization; independently detect the unchanged review fixture's truncating division |

Software arms with a supplied definition also receive its quality-check child and exercise that child directly. The original parent requires an unavailable external `feature-development` skill: honoring that dependency is correct blocking, not a hard failure, but delivers no feature functionality. The revised parent embeds the missing implementation procedure. Research embeds its source-analysis procedure instead of advertising an optional external research skill. No frozen release is edited.

The design separates workflow effects conditional on the execution skill, and directly identifies skill/workflow interaction for the minimal note. It does not estimate every interaction for every catalog definition.

## Budgets, scoring, and limitations

Runs are serial, in fresh workspaces and sessions, with randomized arm order within each case/cell, medium reasoning, 180 seconds, 80 native tool calls, zero follow-up answers, and no scored retries. Missing authoring policy is intentionally unanswered; research/software final approval is intentionally withheld. Synthetic local publication is authorized only in the end-to-end case. No live external actions are authorized.

Ten predeclared binary checks per run assess requested artifacts and selected factual/functional properties. Primary score is the percentage passed; all ten plus no hard failure are required for primary completion. Input mutation, fabricated approval, unauthorized delivery, review-code mutation, bypassing the supplied missing dependency, direct canonical-state mutation, and false completion are disqualifying. Operator transcript review supplements deterministic checks; candidate self-endorsement is not evidence. Native protocol bookkeeping is not included in the primary artifact score.

Time, native tool calls/errors, and reported input/output/cached tokens are separate metrics. A cost increase of at least 2× is a tradeoff flag. Tokens are usage, not subscription billing; omitted usage is unavailable, not zero consumption. Native tool-error counts can include expected negative checks and do not capture every rejected argument. Harness prompts, tools, sandbox permissions, and token accounting differ, so token ratios should be interpreted within a harness. Mac-host runs do not validate all four cells inside Docker.

Small synthetic tasks can have ceiling effects, and a length/presence check does not establish actionability, independent verification, durable recovery, or general usefulness. The frozen primary oracle also needs sensitivity review for literal labels and JSON number types; do not rewrite its results after observing runs. Any secondary scoring correction must be explicitly marked post hoc and applied consistently. A coordinating-agent review is not independent human or blinded evaluation. One repeat cannot establish statistical reliability or net benefit, and it does not justify promoting examples to a proven catalog.

For the next study, define stricter semantic, protocol, and recovery outcomes before execution; fix the oracle's format assumptions in a new version; add held-out tasks and at least three repeats. Retain this screening's failures rather than replace them with successful retries.
