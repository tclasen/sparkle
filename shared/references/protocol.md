# Portable workflow contract

The helper checks structure and evidence paths; the agent interprets instructions, assesses quality, and verifies actual consent. Python 3.11+ and uv are required. `uv run /absolute/skill/scripts/workflow.py …` installs PyYAML from inline dependency metadata. All data paths resolve from the user's repository.

## Documents

Each WORKFLOW.md starts with one YAML mapping: `schema: 1`, `id`, `inputs`, and `steps`. Inputs map stable names to `{required: true}` or `{default: value}` (both may be present). PROJECT.md starts with `schema: 1`, `id`, and `input_defaults`, a mapping from workflow IDs to input mappings. Unknown structural fields and duplicate keys are errors. Values must be JSON-compatible; object constructors, recursive aliases, timestamps, and nonfinite numbers are rejected. Environment inventories, results, state, and release manifests remain JSON.

Step IDs match Markdown headings (`## prepare — Prepare`, nested headings for iteration bodies). Every step has Task, Inputs, Outputs, Acceptance paragraphs. Add Fallback for optional skills, Approval scope for approval steps, and Retry policy when bounded automatic retries are intended. Workflow prose includes onboarding, execution interaction policy, and `## Completion criteria`. Meaning and actual permission remain the agent's responsibility.

Common step fields: `id`, `type`, `depends_on` (IDs within the same scope), `when` (list of `{decision, branch}`), `join` (`all-active` or `selected`), `selected_dependencies`, `skills` (list of `{name, required}`), `capabilities` (strings). Types:

- `task`: perform and assess the work.
- `decision`: `branches` names and `selection: one` (default) or `many`; completion needs `choice` list and `reason`.
- `approval`: completion needs `approval` with `by`, `scope`, `result`, `approved_at`, and local `evidence`. This record does not establish consent.
- `subworkflow`: `workflow: {id, version}` with an exact MAJOR.MINOR.PATCH pin; `inputs` maps child names to literal values or `{input: parent-name}` bindings. Parent completion needs `final: {passed: true, assessment, evidence}`.
- `iteration`: positive `max_iterations` and nested `steps`. Each completed round needs an exit assessment; the last failed exit blocks the container and run. Retry never resets bounds.

Graphs are acyclic within each scope. Guards require the decision as a dependency. Unselected branches are structurally skippable. Ordinary skipped dependencies propagate skips; explicit joins accept terminal active dependencies (selected joins examine only named dependencies). Run ready to obtain the deterministic classification before dispatch. Input precedence is workflow defaults, project defaults, explicit overrides. Composition closure, inputs, project context, environment and definitions are frozen at start. Release SHA-256 hashes detect alteration, not authenticity or filesystem immutability.

## Commands

Prefix all commands below with `uv run /absolute/skill/scripts/workflow.py`.

```sh
inspect FILE
validate FILE --root .
publish FILE --root . --version 1.0.0
verify-release WORKFLOW 1.0.0 --root .
project PROJECT --root . --brief 'Purpose and context'
start PROJECT WORKFLOW --root . --environment environment.json --inputs inputs.json --owner SESSION
status RUN
status RUN --json
ready RUN
context RUN /steps/prepare
validate-run RUN
claim RUN --owner SESSION
release RUN --owner SESSION
```

`start` uses the highest numeric published version unless `--version` is supplied. Publication requires user authorization and never overwrites a destination. `inspect` summarizes inputs and the complete step tree. `status` is concise; `--json` returns state and readiness. `ready` and `context` are read-only. Context includes workflow policy, relevant task prose, final criteria, frozen project/inputs, predecessor results, current attempts and artifact references; it does not interpret instructions.

All state mutations require `--owner SESSION --revision N`, using the revision from status/ready or the preceding mutation. A mismatch rejects the operation without changing state. JSON Pointer paths returned by ready/status identify steps, including `/steps/refine/rounds/0/steps/check` and `/steps/quality/steps/check`. Copy returned paths; do not construct them manually.

```sh
step RUN POINTER begin --owner SESSION --revision N
step RUN POINTER complete --result result.json --owner SESSION --revision N
step RUN POINTER fail --result result.json --owner SESSION --revision N
step RUN POINTER block --result result.json --owner SESSION --revision N
step RUN POINTER skip --result result.json --owner SESSION --revision N
step RUN POINTER retry --result result.json --owner SESSION --revision N
step RUN POINTER reconcile --result result.json --owner SESSION --revision N
round RUN POINTER open --owner SESSION --revision N
round RUN POINTER assess --result round.json --owner SESSION --revision N
finish RUN --result final.json --owner SESSION --revision N
cancel RUN --reason 'User cancelled' --owner SESSION --revision N
```

Begin records an attempt before work. Its optional result can declare external actions as `planned`. Complete requires `assessment` and nonempty `evidence` paths under the run. Fail, block, and skip require `reason`. Retry requires `authorization` identifying the actual user request or applicable bounded policy, and preserves prior attempts. A blocked running attempt may be completed or failed after inspection; retry requires first ending it. Reconcile supplies the complete ordered `external_actions` list, preserving identities and settled receipts. Every action has `description`, `status` (`planned`, `uncertain`, `confirmed`, `not-performed`), and `reconciliation` before retry. Completion requires all actions settled. Save actual receipts as evidence. See [result template](../assets/result.json).

Round assess accepts `{exit_met: boolean, assessment: string, evidence: [path]}` only after all applicable children finish. Open creates the next bounded round only after a failed exit. Finish accepts `{passed: true, assessment: string, evidence: [path], handoff: string}` after all applicable steps finish. Cancellation preserves artifacts and cancels unfinished descendants; it does not roll back actions. Inspect and reconcile in-flight actions before cancellation; report unresolved effects.

Mutations use an exclusive lock, owner and revision checks, transition/history validation, a journal proposal, and atomic state replacement. A crash may leave a journal proposal without a committed revision. Never edit canonical state or use candidate whole-state files. Completed/skipped work and terminal runs cannot change. Validation errors are JSON diagnostics containing stable `code`, `severity`, document/step `location`, `explanation`, and `suggested_correction`. Codes: WF_DUPLICATE, WF_FIELD, WF_PROSE, WF_YAML, WF_INVALID, RUN_REVISION, RUN_OWNER, RUN_EVIDENCE. Validation checks constraints, not semantic quality.

## Optional peer coordination

See the [external ticket protocol](coordination.md) for `start --coordination FILE`, immutable bindings, append-only event commands, recorded readiness blockers, publication and recovery. Unbound runs are unchanged.
