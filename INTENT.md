# Product intent

This document records the purpose, requirements, and boundaries of sparkle, a project for portable natural-language workflows. It captures the current design intent, not a promise of additional features. Update it alongside changes that alter these commitments so their rationale stays reviewable in Git.

The [README](README.md) explains installation and use. The [protocol](shared/references/protocol.md) specifies formats and commands. This document explains what those mechanisms are meant to achieve.

## Purpose

Help people turn a conversational description of repeatable work into a procedure that AI agents can reuse across projects, with explicit versions, visible progress, evidence, and a practical way to continue after interruption.

A chat transcript alone makes it difficult to distinguish reusable instructions from project context, know which instructions governed a result, or recover partial work without losing history. The product makes those distinctions durable and inspectable in ordinary repository files.

## Intended users and experience

Workflow authors describe goals, decision rules, deliverables, and constraints in natural language. Project users supply context and ask an agent to run a published workflow. Contributors maintain the portable skills and the structural helper that supports them.

Users should be able to start with a plain-language request. Agents inspect existing context, ask short rounds of relevant questions, and prepare the required documents. Users should not have to write JSON, assemble a technical brief, or understand the state model before getting useful work done.

## Core design

- **Workflow:** reusable step logic, acceptance criteria, interaction policy, and declared inputs.
- **Release:** an explicitly published workflow version, with hashes and exact references to composed workflows.
- **Project:** reusable context and defaults for a body of work, without changing workflow logic.
- **Run:** a particular execution with frozen context and definitions, progress records, attempts, assessments, and artifacts.

Agents decide what prose means and whether work meets its criteria. The helper enforces structural constraints and focused state transitions. Keeping these responsibilities explicit supports natural-language procedures without pretending prose is a deterministic executable language.

## Requirements

### Authoring and publication

- Support conversational drafting, review, revision, and forks.
- Record goals, inputs, deliverables, acceptance criteria, work boundaries, and an execution interaction policy before publication.
- Make the policy state when to ask the user, use agreed defaults, or stop with a blocker. Do not impose one uncertainty policy on every workflow.
- Require explicit authorization to publish. Preserve existing session authorization without adding repetitive confirmation steps.
- Never overwrite published versions through the protocol. Changed step logic requires a new release or fork.

### Execution and composition

- Support tasks, decisions, explicit approval steps, dependency joins, bounded iteration, and exact-version subworkflows.
- Keep dependencies acyclic within a scope and validate branch and join structure.
- Resolve inputs in order: workflow defaults, project defaults, then explicit run overrides.
- Freeze definitions, composition closure, project context, inputs, and environment inventory at run creation. New context must not silently change existing runs.
- Discover capabilities and skill identities. Missing required capabilities block affected work; optional skills have declared fallbacks.
- Support serial foreground execution without requiring delegation or a background service.

### Durable progress and recovery

- Store readable repository-local documents and JSON records, with artifacts and evidence attached to runs.
- Protect mutations with ownership, revision, locking, and transition checks, and preserve a journal and attempt history.
- Require assessments and evidence for completion. Structural evidence checks do not substitute for an agent's evaluation of the work.
- Support status, interrupted-run recovery, authorized retries, and cancellation without resetting bounds or discarding prior attempts.
- Reconcile uncertain external actions before retrying. Preserve terminal run states and artifacts; do not imply cancellation reverses external effects.

### Optional peer coordination

- Permit independent runs on separate machines to exchange best-effort claims, dependencies, results and handoffs through existing ticket tools. One ticket owns one work unit; never merge run states.
- Freeze ticket bindings and preserve append-only local observations. Recorded conflicts, unobserved claims and unassessed dependencies block new work. Agents perform live rechecks and assess external evidence.
- Require result publication before coordinated completion; preserve recoverable uncertainty and allow cancellation despite failed release notifications.
- Claims are advisory, not exclusive locks. No central dispatcher, provider SDK, automatic takeover or exactly-once guarantee is introduced. Serial foreground execution remains the default.

### Project releases

- Start project releases at v0.1.0, with Conventional Commits determining semantic version increments. Project versions are separate from published workflow definitions.
- Before 1.0, do not require backwards compatibility or regression testing. Continue validating current structure, installation and release tooling.
- Require explicit reviewed promotion to 1.0.0; at and after that milestone assess public-contract compatibility and require regression testing. Breaking changes before promotion remain within 0.x.
- Preserve published tags and assets; release automation must remain locally verifiable and respect protected main without writing release commits to it.

### Portability and maintainability

- Ship two self-contained Agent Skills. Each installed folder must work independently of the source repository and the other skill.
- Keep shared resources canonical and generate deterministic copies into both bundles.
- Use safe YAML parsing for document metadata, Markdown for prose, and JSON for runtime records.
- Verify public CLI behavior and actual installation isolation, including that packaged resources remain complete.

## Boundaries and non-goals

The current product does not include a scheduler, hosted orchestration service, provider SDK integration, built-in tracker integration, automatic shell hooks, DOT support, or an interpreter that executes workflow prose. It does not provide old-format readers, migration commands, candidate whole-state editing, or compatibility aliases.

Hashes detect alteration; they do not provide authenticity or filesystem-enforced immutability. Snapshots preserve recorded inputs and instructions, not identical agent judgments or future tool availability. Referenced external content needs separate capture when relevant.

The helper cannot prove actual consent, prose truth, result quality, or external action outcomes. Those remain the coordinating agent's responsibility, supported by user authorization and concrete evidence. Approval gates must have meaningful scope; a generic gate is not required for every workflow.

## How to assess changes

Judge proposed skill/product changes through paired usefulness evaluations across local Ollama `gpt-oss:120b` and subscription Luna 6.0 (`gpt-6-luna`), each with Codex CLI and the Pi coding harness. Include the initial comparison from no skills to the current product. Measure deliverable utility, correctness, consent compliance, user effort, and resource tradeoffs; structural validity alone does not establish improvement. The [evaluation policy](docs/EVALUATIONS.md) records this requirement. Configuration smoke tests establish readiness only; the initial usefulness comparison remains pending.

A change should make it easier to author, reuse, inspect, or recover a workflow while preserving the distinction between agent judgment and structural enforcement. Check whether it keeps installed skills independent, preserves evidence and frozen context, and leaves users with an understandable next action when work cannot proceed.

When changing a requirement or boundary, update this document in the same contribution. Explain the problem, new intended behavior, tradeoff, and how the behavior will be verified. Mark future proposals explicitly rather than presenting them as existing capabilities. Git history and the contribution description should retain the reason for the decision.
