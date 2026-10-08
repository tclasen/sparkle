# Conversational walkthroughs

These exercises use simulated local evidence, not claims of live research, deployment or user approval. Prefix helper commands with `uv run /absolute/skill/scripts/workflow.py`. Each mutation needs the current `--revision N` and `--owner SESSION`; read commands return paths and revisions.

## Minimal linear run

1. User: “Prepare a note about our launch.” Resolve audience and topic from context, asking only gaps. Publish [the linear workflow](minimal-linear/WORKFLOW.md) only when requested.
2. Create a project and save its context. Save topic overrides as JSON and discover an environment inventory. `start PROJECT example-workflow --inputs inputs.json --environment environment.json --owner SESSION` returns RUN.
3. `ready RUN` returns `/steps/prepare`. `context RUN /steps/prepare` provides frozen instructions and inputs. `step RUN /steps/prepare begin` persists the attempt before drafting.
4. Write the note under RUN/artifacts. Save a result JSON with assessment, relative evidence paths, external actions, blockers and handoff. `step RUN /steps/prepare complete --result result.json` records it.
5. Read ready/context for check; begin, perform the review, and complete it with its own assessment. No state editing is needed.
6. `finish RUN --result final.json`, where final contains `passed: true`, assessment and evidence. Validate the run, report artifact paths and limits, and release ownership.

## Branches, approval and iteration

[Research-to-deliverable](research-to-deliverable/WORKFLOW.md) demonstrates decisions, optional skill fallback, an active join, bounded refinement and an explicit approval gate. Complete the decision with named choices and reason. Ready identifies excluded paths as skippable; record each skip reason. Begin only ready active branches. Missing required capabilities block affected work; optional skills follow the step's Fallback.

Begin the iteration container and use `round RUN POINTER open`. Ready returns child paths including the round index. Complete children and use `round … assess --result FILE` with exit_met, assessment and evidence. A passing exit permits container completion; a failing exit permits another round within the bound. Exhaustion blocks the run and never resets the count.

At an approval step, prepare the exact deliverable and scope, obtain actual consent unless already authorized, and save its reference locally. Complete with approval fields by, scope, result, approved_at and evidence. A fixture approval object is not permission in a real run.

## Composition and authorized delegation

Publish [quality-check](software-feature/quality-check.md) first, then [software-feature](software-feature/WORKFLOW.md). The parent pins the child release and binds its inputs. Begin the parent container, then use child paths returned by ready/context. Assess child completion criteria and supply a final assessment when completing the container.

Execution is serial by default. When delegation is authorized, give each worker context, acceptance, boundaries, unique artifact paths and the common result contract. Persist the attempt before dispatch. Workers return results; the sole coordinator assesses and commits them.

## Interrupted work

Read status, validate snapshots, and establish that the old coordinator stopped before taking ownership. Claim with its exact prior identity and stopped evidence. Inspect action receipts and outputs through context. Use reconcile to settle planned/uncertain actions without changing identities. Fail an unsuccessful running attempt before retry; provide authorization from the user request or a declared bounded retry policy. Do not repeat confirmed external effects. Cancellation preserves artifacts and cancels remaining descendants, without rollback. See the installed recovery reference for stale-lock handling.

## Two machines coordinating through tickets (simulation)

This walkthrough and the public CLI fixtures simulate ticket observations. They do not exercise a live provider or prove its consistency, durability, permissions, or retry behavior. A live integration check needs an explicitly designated test ticket and available read-history/write-message tools.

1. Machine A and machine B have isolated clones, the same published definitions, and independent local runs. Normally A binds ticket T-1 and B binds T-2, with unique claim IDs and declared shared resources. Each saves a claim intent, publishes its run/claim/scope, rereads history, and records an accessible claim observation. `ready` reports `observed-without-conflict` only after required dependency assessments pass.
2. To simulate a race, both instead bind T-1. A reads only claim A; B reads only claim B. Both can begin. This demonstrates the remaining duplicate-work risk: advisory claims do not implement mutual exclusion. The fixture never performs real external actions.
3. Each later reads both claims. The observation records a persistent conflict. A fails its interrupted attempt; retry is rejected. A later read showing only A still does not resolve the recorded collision. B publishes withdrawal. A saves that receipt and records a `resolution` referencing the conflict event with `mode: withdrawals` and B's claim in `withdrawn_claims`. Explicit user resolution is an alternative requiring actual evidence. Neither an old timestamp nor a quiet session establishes withdrawal.
4. T-1 depends on T-parent. A closed T-parent without an assessed result remains blocked. A saves linked result/evidence and records an accepted dependency assessment only after checking applicability. Cycles or missing evidence receive rejected assessments. An unavailable ticket tool produces an inaccessible observation and blocks affected work until access and a fresh observation recover.
5. A claim write loses its response. The saved intent includes the stable message ID. The agent inspects history before retrying, finds the message, and records the observation. If inspection fails, it waits; it cannot infer that the write failed. For result publication, save `planned`, then inspect and record `uncertain` or `confirmed` using the same message ID and `inspected: true`. The helper cannot verify that inspection happened; local evidence supports the agent's judgment.
6. A completes its steps and assesses the final result. `finish` fails until a confirmed `result_publication` includes that exact final result, accessible evidence references and the external receipt. Repeated receipts preserve the message payload. Failed publication leaves the run recoverable. After confirmation, finish succeeds; further coordination mutations are rejected.
7. For an interrupted handoff, save the intended successor and stable message ID. An uncertain receipt blocks new work. Inspect the ticket before retrying or recording confirmation. The successor starts its own run with predecessor evidence; it never merges A's state. Moving A's actual run requires complete records and stopped-owner evidence under the existing recovery protocol.
8. B may cancel even if its release notification fails. It records the uncertain release receipt first, then cancels locally, preserving all evidence. Another peer must explicitly reconcile B's stale ticket claim before continuing; cancellation is not rollback or proof of external release.

The automated equivalents are `test_coordination_binding_isolation`, `test_coordination_records`, `test_peer_races_dependencies_and_recovery`, and `test_publication_uncertainty_handoff_and_cancellation` in `tests/test_workflows.py`.
