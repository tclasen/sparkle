# Agent-led onboarding interview

The agent owns information gathering and file preparation. Accept a plain-language starting point; do not ask the user to complete a template, assemble all requirements, choose technical IDs, or write JSON. Discover facts from available repository instructions, definitions, project notes, and session answers before asking about preferences or missing facts. Never treat example values or unanswered questions as user decisions.

## Adaptive conversation

1. Identify the operation and inspect relevant existing context. Derive routine names and paths where unambiguous. Ask only when selecting among plausible workflows/projects would change the work.
2. Track known answers, their source, and unresolved execution-relevant gaps. Reuse current answers; ask about conflicts or changes without repeating the whole interview.
3. Ask one to three related questions per round in plain language, with concrete options or a suggested default when helpful. Start with goals and outcomes, then ask about decisions and constraints. Adapt the next round to the answers. Use an available question tool or ordinary conversation; no particular host tool is required.
4. Distinguish reusable workflow behavior, project context, and one-run inputs. The agent translates answers into the existing Markdown/JSON formats. A missing run-specific topic need not block authoring a reusable workflow; specify how project/run onboarding will collect it.
5. Summarize the recorded choices and remaining gaps. Continue already authorized work when ready; do not add a universal “approve onboarding” gate. An unanswered required question remains unresolved. Continue independent preparation where possible, but do not begin dependent execution.

## Workflow author interview

Cover only relevant gaps in these areas:

- Purpose, audience, deliverables, output destinations, and observable acceptance/final criteria.
- Required inputs, reusable defaults, source/reference requirements, and information to collect during project/run onboarding.
- Step dependencies, branch decision criteria, handoffs, composed workflows, and optional-skill fallbacks.
- Work boundaries, external side effects, authorization scope, concrete approval gates, iteration exit criteria/bounds, and retry conditions.
- The user's execution interaction policy for this particular workflow.

Ask, for example: “If new uncertainty appears while this workflow runs, when should I ask you, use a default we agree now, or stop and leave a blocker?” Follow up until the policy specifies the triggers, permitted defaults or decision rules, and what to do when those rules do not cover a case. Users may choose different rules for different types of uncertainty. Do not silently choose one policy for all workflows. Record any allowed project-specific policy choices explicitly. Approval gates remain separate: onboarding cannot approve an unseen future deliverable or action whose scope requires later review. Preserve actual authorization already given.

Store reusable behavior and this policy in workflow prose. Put declared input defaults in YAML front matter. Walk branches and failure paths to find questions that can be settled now. Existing drafts receive gap interviews; published definitions require a draft revision and explicit publication to change behavior. For review-only requests, report gaps and suggested questions without editing.

## Project and run interview

Read the selected published version (highest numeric version if omitted), its composed definitions, the project, relevant repository instructions, and existing answers. Identify required inputs using workflow defaults, project defaults, and explicit run overrides in that order. Check semantic constraints in prose as well as missing values. Inspect tools and capabilities yourself instead of asking the user to inventory them.

Collect missing purpose, audience, success criteria, input references, output destinations, work areas, constraints, and run inputs. For an existing project, ask only about absent, changed, or conflicting details. For each answer whose reuse is unclear, establish whether it is a project default or applies only to this run. A user's request to update project context authorizes that update; merely inspecting status does not.

Store reusable context and decisions in `PROJECT.md`, with reusable declared inputs under `input_defaults` keyed by workflow ID. Write one-run overrides to a local input file for `start --inputs`; do not silently promote them to project defaults. Record concise decisions and their source (user answer, repository fact, or applicable existing default), not a mandatory full transcript. Use project inputs for supporting references. The `project` command creates a skeleton; the agent must fill the template's additional prose sections before start.

Follow the workflow's interaction policy. Project notes may select only options the workflow explicitly allows; they cannot replace its step logic or gates. If a published workflow lacks the policy, explain the gap and route to workflow revision before a new run; never edit the release or publish without authorization. Existing runs remain governed by their snapshots and must not be retrofitted with new onboarding answers.

## Readiness and execution

Before finalizing authoring, ensure behavior, acceptance criteria, input collection guidance, decision rules, boundaries, and the interaction policy are sufficiently specified to execute. Before `start`, ensure required inputs and project choices are resolved and recorded. Record missing capabilities as blockers under the existing execution protocol; do not confuse capability blockers with unanswered interview questions. Structural validation cannot establish interview completeness.

During execution, consult saved context first. Apply the recorded interaction policy and journal the rule and outcome. If the policy says to ask, ask the focused question; if it permits a default, use that default; if it says to stop, record a blocker and handoff. A consequential case outside the policy remains blocked rather than silently decided. An answer that changes frozen inputs or workflow behavior requires a new run and, where applicable, a new release. Preserve required approval gates and permission scope regardless of any preference to avoid later questions.

Resume/retry uses the frozen context, evidence, and recovery protocol rather than restarting onboarding. A legacy run without an interaction policy keeps its existing instructions; do not invent new authority. Status and cancellation require no interview. Onboarding aims to resolve foreseeable questions, while unforeseen issues and concrete approvals follow the user's chosen workflow rules and existing authorization requirements.
