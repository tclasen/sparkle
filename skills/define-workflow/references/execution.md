# Coordination, evidence, and recovery

## Questions during execution

Use the frozen workflow's user-defined interaction policy and saved project/run answers. Apply agreed rules, ask, or stop with a blocker as that policy directs; journal the relevant rule and outcome. Do not restart onboarding during recovery or silently change frozen inputs. Required concrete approval gates and existing authorization still apply. See [the onboarding interview](onboarding.md) for authoring and pre-start readiness.

## Bounded worker assignment

Delegate only when the current user/environment permits parallel agents. Give each worker the run ID and pinned definition, eligible step ID, frozen inputs/context, exact work area and permitted mutations, acceptance criteria, unique artifact directory (`artifacts/<step>/<attempt>/<worker>/`), and reporting format. Specify forbidden overlapping mutations, external-action limits, and approval gates. A worker reports status, files produced, criteria assessed, evidence, external actions and receipts, blockers, and recovery notes. It never changes canonical state, owner markers, or another worker's artifacts.

The coordinator checkpoints each running attempt before dispatch. Review worker outputs and evidence, reject incomplete results, and checkpoint accepted outcomes in dependency order. A worker's claim of success is not a completion assessment. If two eligible steps mutate the same work area, serialize them unless isolated worktrees or directories were explicitly established. Without delegation, the coordinator executes the same assignment contract serially. Prose conditions are judged by the agent in both modes.

## Recovery walkthrough

1. Read status without claiming. Check snapshot integrity. Inspect the owner marker, confirm the old coordinator stopped (e.g. explicit session termination or a release), and claim with evidence. A quiet session or old timestamp is insufficient.
2. Inventory unfinished attempts, artifacts, and external-action receipts. Compare actual changes with prior acceptance criteria. Preserve completed/skipped records exactly. Record observed tool/skill changes in the journal; a frozen inventory does not guarantee current availability.
3. For an interrupted running attempt, continue it only after reconciliation. If its work already meets criteria, assess and complete it with recovered evidence. If it failed, checkpoint failure and a reason. Set actions with unknown outcomes to uncertain. Record inspection and make them confirmed or not-performed before any new attempt. Keep completed external actions out of retry work.
4. Wait for user retry instructions unless the pinned step declares a retry policy that applies. Record the exact policy/request, bounds, and current attempt count. Append one running attempt, record the authorization, in a result file as `authorization`, then use `step … retry --result FILE`. A failed action's reconciliation can be added without changing its original outcome/evidence. Do not infer authorization from waiting.
5. A failed iteration exit at its last bound blocks the container and run. A retry does not reset the round count or extend the bound. Revise the workflow and start a new run if a higher bound or changed logic is needed.
6. When yielding, record the next safe action, pending approval scope, work-area state, and uncertain external effects in the journal; release ownership if the session is stopping. A status report may leave a live coordinator in place while it continues.

For an approval, prepare the concrete deliverable/action, put its reference and scope in a local file, request user approval if not already authorized, and pause dependent work until the answer arrives. Save the actual answer/reference locally. Neither a fabricated approval object nor an agent assertion constitutes user consent.

Cancellation requests authorize stopping dispatch, not destroying work or reverting external actions. Inspect dispatched work, preserve outcomes/evidence, cancel all remaining descendants with reasons, and report any external actions still uncertain. Do not claim rollback or cancel an external job unless within the requested scope.

Use `status`, `ready`, and `context` to inspect. Every focused mutation requires the current `--revision` and `--owner`. Claim a previously owned run with `claim RUN --owner NEW --prior-owner OLD --prior-stopped-evidence TEXT`. If a crash left `.mutation.lock`, establish all writers stopped, journal the evidence, and remove only the stale lock before claiming. Never bypass a live coordinator.

## Independent peers on different machines

Follow the [external ticket protocol](coordination.md) for optional ticket bindings and durable messages. Each peer coordinates its own run in an isolated work area. Never merge state copies. Read ticket history and dependencies before claiming, reread after publication, and recheck before each step and shared action. Record missing access, dependency evidence, resource collisions and competing claims. Explicit withdrawals or actual user resolution clear conflicts; timestamps do not. An observed uncontested claim is advisory and can still race another peer.

Local `ready` distinguishes unobserved claims, unavailable tickets, unresolved conflicts, unassessed dependencies, released claims and observed claims without conflict. These checks gate begin/retry/round-open but cannot enforce live external reads or semantic assessments. Existing attempts may be reconciled while blocked; starting further external work remains forbidden by the agent protocol.
