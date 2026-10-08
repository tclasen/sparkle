# Evaluate whether the skills help

## Intent and required matrix

Evaluate both `define-workflow`/`execute-workflow` and the pre-authored workflow definitions currently under `examples/` on their ability to produce useful results. A proposed change needs observed evidence of net benefit before it is accepted on that basis. Plausible prose, a model's endorsement, successful structural validation, and passing unit tests do not establish that benefit. The examples are candidates for an intentional workflow catalog; their current name or inclusion does not establish effectiveness.

Use every combination below for each proposed skill or product change. Keep the four cells separate in reports.

| Model | Codex CLI | Pi coding harness |
| --- | --- | --- |
| Local Ollama `gpt-oss:120b` | Required | Required |
| OpenAI subscription `gpt-6-luna` (Luna 6.0) | Required | Required |

`gptoss:120b` in conversational requests means the installed Ollama model tag `gpt-oss:120b`. Luna uses subscription OAuth, not a paid OpenAI Platform API key. Do not silently substitute another model, authentication route, or harness when a cell fails. See [configuration and preflight evidence](EVAL_CONFIGURATION.md).

This is a contributor evaluation policy, including before 1.0. It complements the structural, installation, and version-dependent regression checks in [Contributing](../CONTRIBUTING.md) and [the release policy](RELEASING.md); it does not change the installed skills' runtime contract. The [initial 64-run screening](evals/2026-10-08-screening/README.md) is complete across all four cells. Its one-repeat artifact checks, mixed results, incomplete definition uptake, and scoring limitations do not establish overall net benefit. Formal repeated utility/adoption evaluation remains pending.

## Define the comparison before running it

1. Write a concrete hypothesis: the user problem, proposed change, expected improvement, likely costs, and outcomes that would disprove it. For every proposal, identify the affected cases and acceptance criteria before looking at candidate results. Avoid changing the rubric to justify a preferred implementation.
2. Pin the baseline and candidate Git commits and hash the actual skill bundles. For ordinary changes, use the previously accepted implementation as baseline. For the initial comparison from nothing to the current implementation, use a **no-skill baseline**: the same task, inputs, native harness tools, and environment, with sparkle skills, bundled helpers, and skill-specific instructions absent. Do not invent an empty historical commit or give the baseline candidate artifacts. Record which resources differ.
3. Use identical task prompts and input fixtures for each baseline/candidate pair. Prompts state the user's goal, constraints, and authorized actions without coaching the candidate through its implementation. Record scripted user answers and approval scopes; provide the same answers when the same gaps arise. Unanticipated material questions go to the evaluator and are recorded, never guessed.
4. Choose useful cases for both skills: authoring from an incomplete request; execution to a usable deliverable; and a complete authoring-to-execution path. Include independently installed skills, relevant negative/recovery cases, and realistic work whose output can be checked against source material or an external oracle. Narrow changes may use a focused case set, but still run it in all four cells. Use held-out cases after tuning.
5. Fix the scoring rubric, hard failure criteria, time/tool/iteration limits, user-intervention budget, repeat count, and adoption threshold. Default to at least three independent trials per case, variant, and cell. One case therefore needs at least 24 runs: four cells × two variants × three trials. Smaller exploratory runs can inform case design but cannot establish the adoption decision.

For catalog evaluations, separate the contribution of the skills from that of the pre-authored instructions. Compare no workflow with a supplied workflow while holding the execution skill fixed; compare original/candidate workflow revisions with the same skill, task, and inputs. Where practical, use the full skills-present/absent × workflow-present/absent design within each model/harness cell. Assess composed children directly when a parent dependency or approval prevents reaching them. Report coverage per definition, not just an aggregate catalog score. Promotion from examples to a proven catalog requires outcome evidence across relevant tasks and failure paths.

## Run controlled pairs

- Run serially in fresh temporary workspaces and fresh sessions. Never resume a baseline session as a candidate. Alternate or randomize baseline/candidate order and record it. Keep inputs, installed dependencies, tools, network access, reasoning settings, and budgets fixed within each cell. Native prompts and tool implementations differ between harnesses; preserve and record those differences.
- Install only the exact pinned bundles under evaluation. Do not expose the source checkout or sibling skill to an independent-skill case. Discover and record the resources actually loaded. Disable unrelated global skills, extensions, MCP servers, hooks, and project instructions, or explicitly declare them as controlled dependencies. Ensure the no-skill condition cannot discover sparkle through ancestor directories or global installations.
- Do not use external skills in these repository evaluations. Expose only the selected repository skills and inspect actual skill reads/invocations. If a harness retains passive global skill descriptions, disclose that limitation and keep them constant; any actual external-skill use invalidates the run. A local workflow missing necessary procedure should embed that procedure in its own instructions rather than depend on an unprovided external skill. Evaluate the original and revised definitions; do not rewrite a frozen run or published release.
- Confirm preflight for all four cells before an expensive batch: selected model/provider, inference, tool read/write, skill access, and required dependency execution. Repeat preflight after changing a harness, model, provider configuration, authentication route, or environment. A successful smoke test does not score skill usefulness.
- Preserve transcripts, tool calls/results, final artifacts, timings, token counts when available, questions, failures, and evaluator assessments outside the source repository. Use synthetic/public fixtures; keep credentials and private user data out of both committed reports and shared evidence. Redact any accidental secret before sharing it.
- Record timeouts, malformed results, refused work, and incomplete outcomes. A rate limit, network failure, unavailable model, or missing credential makes a cell blocked; it is not evidence of a poor skill. Retain failed attempts and retry only under the recorded policy. Never select only the successful retries.
- Use the helper's public commands for mutations. Do not edit run state to make acceptance checks pass. Scripted consent fixtures are simulated authorization; do not present them as real user approvals or external outcomes. External-effect cases need explicitly authorized test resources and reconciliation before retries.

## Judge useful outcomes and make the decision

Inspect artifacts and the work needed to use them, not just the agent's final claim. Assess task correctness, completeness, source-grounded truth, actionability, instruction/consent compliance, recovery, and unnecessary user effort. Record latency, token usage, tool calls, and resource costs separately. Subscription tokens are usage, not an invented per-token API bill; local inference still consumes time and compute.

Use a case-specific rubric with a common utility scale: **0** no usable result, **1** major repairs needed, **2** useful after substantial edits, **3** useful after minor edits, **4** usable as delivered. Specify what each level means for the actual deliverable. Structural checks support scoring but cannot award semantic quality. Unauthorized actions, fabricated evidence, corrupted/frozen records, and false completion claims are hard failures regardless of the utility score.

Have an evaluator review baseline/candidate artifacts with variant labels hidden and order shuffled where practical. Record the evaluator identity, rubric, rationale, and disagreements. An agent may assist scoring, but candidate self-assessment alone is insufficient; inspect the actual evidence and uncertain judgments. Do not treat the small default sample as statistical proof.

Report paired utility deltas and success counts per case and cell, the spread across trials, hard failures, and changes in effort/time/resources. Weight cells equally if presenting an overall average. Before execution, define material regression and acceptable cost increases for the task. The default decision requires positive average paired utility improvement, no material regression in any cell, no candidate hard failures, and costs within the declared budget. A tie, missing cell, noisy result, or tradeoff without a declared acceptance rule is **inconclusive**, not a demonstrated net benefit. Improve the proposal or collect more evidence before claiming it helps.

## Evaluation record

Each comparison report must contain:

- Hypothesis and proposal scope; baseline/candidate commit IDs, bundle hashes, and no-skill resource exclusions where applicable.
- Case/input/prompt versions and hashes, authorized actions and user-answer script, rubric, thresholds, budgets, repeat count, run order, and evaluator identity.
- For every run: cell, trial, variant, harness/version/install source, requested and observed model/provider/authentication route, model digest or available revision metadata, configuration, actual loaded skills/tools, workspace isolation, reasoning/sampling settings, context limits, timestamps, exit status, and evidence location.
- Per-run utility and hard failures with evidence; tokens/time/tool calls/user effort; per-cell paired comparisons; infrastructure blockers and all retries.
- A decision of benefit, regression, or inconclusive, with limitations and the next action. Attach a sanitized summary and accessible evidence references to the change review. Preserve raw evidence outside the repository according to its retention/privacy constraints.

## Next evaluation

Version a corrected oracle and clarify ambiguous prompt/count scopes using the screening's recorded limitations. Compare **no sparkle** with the currently accepted skills in all four cells on held-out tasks, and separately assess the pre-authored workflows and proposed revisions. Evaluate each skill alone, the two-skill path, actual definition uptake, repeated reuse/recovery, and independently assessed utility with at least three repeats. Screening with fewer than the default repeats remains provisional and cannot establish a proven catalog or adoption decision. Record configuration preflight separately; the dated screening snapshots are evidence, not a general-purpose automated evaluator.
