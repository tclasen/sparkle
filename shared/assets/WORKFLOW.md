---
schema: 1
id: example-workflow
inputs:
  topic:
    required: true
steps:
  - id: prepare
    type: task
  - id: check
    type: task
    depends_on: [prepare]
---
# Prepare a deliverable

## Goal and deliverables
Create a short local note about the supplied topic and check its clarity.

## Onboarding and input collection
Ask for the topic if it is missing. Establish audience and intended use from existing project context or a short gap question.

## Execution interaction policy
Use saved project context for presentation choices. If an ambiguity changes the intended meaning or requires an external action, ask a focused question and block dependent work until answered. This workflow authorizes local drafting and checking.

## prepare — Draft the note

Task: Write a concise note about the topic for the agreed audience.
Inputs: Frozen topic and project audience/context.
Outputs: A local note under artifacts/ and a result referencing it.
Acceptance: The note addresses the topic, identifies assumptions, and fits the audience.

## check — Check the note

Task: Review the note and correct unclear wording or unsupported assertions.
Inputs: The prepare result and its artifact references.
Outputs: Final note and review evidence under artifacts/.
Acceptance: The note meets the agreed purpose and has no unresolved substantive concerns.

## Completion criteria
The final note and review evidence are saved and both step assessments pass.
