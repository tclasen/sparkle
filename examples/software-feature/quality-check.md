---
schema: 1
id: quality-check
inputs:
  repository:
    required: true
steps:
- id: inspect-code
  type: task
  capabilities:
  - repository-read
- id: run-tests
  type: task
  capabilities:
  - shell
- id: quality-summary
  type: task
  depends_on:
  - inspect-code
  - run-tests
  join: selected
  selected_dependencies:
  - inspect-code
  - run-tests
---
# Feature quality check

## Goal
Assess the changes in repository. This workflow reviews and tests; it does not merge or deploy.

## Onboarding and input collection
Resolve repository and expected behavior from parent inputs/context when composed. When run directly, discover the repository and interview for missing change scope and acceptance criteria before start. Inspect repository check instructions rather than asking the user to list commands that can be discovered.

## Execution interaction policy
For this example, the authoring interview selected: use repository instructions to choose checks; if missing context, unavailable tools, or unexpected ambiguity prevents assessment, record a blocker and handoff without asking execution questions. Do not silently weaken checks or infer permission for new external actions.

## inspect-code — Inspect correctness

Task: Read the repository's instructions, expected behavior, and changed code. Independently derive counterexamples for boundary values, empty inputs, invalid inputs, and interacting conditions; do not rely only on examples supplied in the request or existing passing tests. Run reproducible checks for suspected defects and record expected versus observed behavior. A plausible concern is not a verified defect. Review is read-only unless the user explicitly authorized a repair.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: record correctness/security concerns and whether each is resolved. Evidence includes the exact commit/diff identity.

## run-tests — Run focused checks

Task: Run meaningful focused tests plus required repository checks. Assess whether the tests would fail for a plausible incorrect implementation. Add independent checks when authorized, or run temporary checks without modifying review code. Preserve failing results and unresolved defects instead of reporting success from a passing smoke test. This may run independently of inspect-code only when no overlapping mutation occurs; use an isolated test work area if necessary.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: checks pass or failures are resolved, commands and exit codes saved locally.

## quality-summary — Consolidate evidence

Task: Assess the checked diff against the requested behavior.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: both selected assessments passed and the evidence corresponds to the same change. Record an explicit summary.

## Completion criteria
The reviewed change has no unresolved correctness concerns and passes required checks with evidence tied to the same diff/commit.
