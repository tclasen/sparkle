---
schema: 1
id: research-to-deliverable
inputs:
  question:
    required: true
  audience:
    default: project sponsor
steps:
- id: research
  type: task
  capabilities:
  - web-search
  skills:
  - name: research
    required: false
- id: choose-format
  type: decision
  depends_on:
  - research
  branches:
  - memo
  - comparison
  selection: one
- id: memo
  type: task
  depends_on:
  - choose-format
  when:
  - decision: choose-format
    branch: memo
- id: comparison
  type: task
  depends_on:
  - choose-format
  when:
  - decision: choose-format
    branch: comparison
- id: refine
  type: iteration
  depends_on:
  - memo
  - comparison
  join: all-active
  max_iterations: 2
  steps:
  - id: audit
    type: task
  - id: revise
    type: task
    depends_on:
    - audit
- id: accept
  type: approval
  depends_on:
  - refine
- id: deliver
  type: task
  depends_on:
  - accept
---
# Research to decision memo

## Goal and deliverables
Produce an evidence-backed memo answering question for audience. Store citations, notes, and memo in this run's artifacts; copy the approved memo into project outputs. Observe source dates and separate facts from inferences. No messages are sent externally.

## Onboarding and input collection
Before start, collect the research question, audience if different from the default, relevant source constraints, and output destination from available context and a gap interview. Save reusable preferences in the project and the question as a run override unless the user wants it reused.

## Execution interaction policy
For this example, the authoring interview selected: choose format using the rule below, use the recorded audience default, and label uncertain evidence without asking when the question can still be answered. Ask a focused question if a new ambiguity would change the intended question or recommendation criteria. If the answer changes frozen inputs, start a new run. For other consequential gaps, record a blocker and handoff. This policy does not remove the final concrete approval or increase iteration limits.

## research — Collect evidence

Task: Search primary sources and save dated URLs and excerpts with source usage limits.
Fallback: use available web search and direct source reading, write a source ledger and assessment without a specialized research skill.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: at least three relevant independent sources, explicit uncertainty, and enough evidence to address the question.

## choose-format — Select the deliverable format

Task: Choose comparison when the question compares alternatives on common criteria; otherwise choose memo. Record the choice and its rationale using research evidence.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: Assess the task criteria above and save supporting evidence.

## memo — Draft a narrative answer

Task: Write a concise answer with evidence, uncertainty, and recommended next action.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: claims have supporting sources and the audience can understand the recommendation.

## comparison — Draft a comparison

Task: Compare options in a criteria table with dated source links and tradeoffs.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: identical criteria across options, transparent unknowns, and a reasoned recommendation.

## refine — Refine until evidence supports the conclusions

Task: Role: editor. Read the selected draft. Exit when every substantive claim has support, conflicting evidence is addressed, and the question is answered. Assess exit after each round with local evidence. If two rounds fail, block for clarification or a new workflow version; do not silently expand the budget.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: Assess the task criteria above and save supporting evidence.

### audit — Check support

Task: List unsupported claims, conflicting sources, and audience gaps.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: every claim traced or explicitly marked uncertain. Save the audit separately for each round.

### revise — Apply the audit

Task: Revise the selected draft using the audit; if no changes are needed, record why.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: each audit item resolved or explained. Do not overwrite evidence from prior rounds.

## accept — Approve the deliverable

Approval scope: Acceptance of the concrete deliverable presented by this step; preserve the actual user response as evidence.

Task: Present the exact revised deliverable. Ask the user to approve it for inclusion in project outputs; this scope does not authorize external distribution. Preserve the user's response and deliverable identity/hash.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: Assess the task criteria above and save supporting evidence.

## deliver — Save the approved memo

Task: Copy the approved deliverable into project outputs, retain a run-local copy and hash as evidence.

Inputs: Frozen run inputs and predecessor results.
Outputs: Local artifacts and a structured result with evidence and handoff.
Acceptance: copied bytes match the approved artifact. Never overwrite unrelated project outputs.

## Completion criteria
The selected deliverable answers the question, the refinement exit criteria passed within two rounds, the user approved that concrete result, and matching copies exist in run artifacts and project outputs.
