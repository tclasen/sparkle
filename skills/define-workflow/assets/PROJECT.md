---
schema: 1
id: example-project
input_defaults:
  example-workflow:
    topic: Example topic
---
# Project title

## Brief
Purpose, audience, constraints, and success criteria.

## Inputs and references
Record relevant input copies or hashes and reference context before starting.

## Work areas
Paths or repository URLs, pinned commits where relevant, allowed mutations, and isolation requirements. Specify how run artifacts become project outputs.

## Onboarding decisions
The agent fills these sections from repository context and a short adaptive interview. Record reusable answers, applicable workflow/version, decision sources, and unresolved gaps; do not treat template examples as answers. Ask only about missing or changed information on later onboarding.

## Workflow-specific choices
Record any project choices explicitly permitted by the selected workflow's execution interaction policy. Refer to that policy without overriding workflow logic or approval gates. Put reusable declared inputs in `input_defaults`; keep one-run overrides separate. Resolve required gaps before starting; existing runs keep their snapshots.
