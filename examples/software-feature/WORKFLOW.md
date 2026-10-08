---
schema: 1
id: software-feature
inputs:
  repository:
    required: true
  feature:
    required: true
steps:
- id: design
  type: task
  capabilities:
  - repository-read
- id: implement
  type: task
  depends_on:
  - design
  capabilities:
  - repository-write
  - shell
  skills:
  - name: feature-development
    required: true
- id: quality
  type: subworkflow
  depends_on:
  - implement
  workflow:
    id: quality-check
    version: 1.0.0
  inputs:
    repository:
      input: repository
- id: review
  type: approval
  depends_on:
  - quality
- id: handoff
  type: task
  depends_on:
  - review
---
# Software feature delivery

## Goal and work boundaries
Deliver feature in the supplied repository with tested code and a reviewable change. Follow that repository's instructions. Record repository path and starting commit in project context. Never merge or deploy in this workflow. Save diff, test evidence, and handoff in run artifacts. Mutations in the repository are coordinated serially unless isolated work areas are provided.

## Onboarding and input collection
Discover the repository from context where unambiguous; interview for the requested feature, observable behavior, constraints, acceptance criteria, and mutation boundaries before start. Record the repository and starting commit in project context. Collect required inputs and inspect the child workflow's requirements before beginning implementation.

## Execution interaction policy
For this example, the authoring interview selected: use repository conventions for routine implementation choices; for unexpected uncertainty affecting feature behavior or scope, stop with a blocker and a handoff instead of asking during implementation. Other consequential cases outside recorded guidance also block. The quality-check child uses its own compatible stop policy. Final review still requests approval of the actual diff. Retry requires the authorization specified below.

## design — Establish acceptance criteria

Task: Inspect the existing implementation, define behavior and focused checks for feature.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: clear before/after behavior, mutation boundaries, and no unresolved ambiguity that prevents implementation. A failure permits one explicit user-authorized retry; there is no automatic retry policy.

## implement — Implement the feature

Task: Use the required installed feature-development skill in the repository work area.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: code implements agreed behavior and is locally reviewable. Capture diff and any external actions before a handoff. Missing required skill blocks this step; do not silently substitute another procedure.

## quality — Review and test

Task: Run the exact quality-check release, forwarding repository. Child artifacts remain in this run.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: child workflow and its final criteria pass for the implemented diff. Serialize test mutations if review/test work areas overlap.

## review — Approve the concrete change

Approval scope: Acceptance of the concrete deliverable presented by this step; preserve the actual user response as evidence.

Task: Present the diff, behavior, and validation to the user. Approval scope: accept this feature for handoff as a reviewable change. This does not authorize merge, deployment, or sending messages. Preserve the response and exact diff identity.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: Assess the task criteria above and save supporting evidence.

## handoff — Produce the final handoff

Task: Write a concise handoff with behavior change, changed files, checks, and limitations. Save the approved diff/reference and handoff in project outputs with run-local copies as evidence.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: handoff corresponds to the approved change and contains test results.

## Completion criteria
The requested behavior is implemented, the pinned quality-check workflow passed, the user approved the exact change, and project outputs contain a complete handoff and change reference.
