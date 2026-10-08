---
name: define-workflow
description: Create, revise, review, fork, and explicitly publish versioned repository-local workflows through agent-led onboarding interviews and conversational requests. Use when users want reusable agent-led procedures with dependencies, decisions, approvals, bounded iteration, or composed workflows.
compatibility: Requires a filesystem and uv with Python 3.11 or later. PyYAML is installed by uv from inline dependency metadata.
metadata:
  version: "unreleased"
---

# Define a workflow

## Activation boundaries
Use for conversational authoring, review, revision, fork, or explicit publication. Work in the user's repository, outside this installed skill. Publication requires an explicit request; creating a draft does not imply publication. Honor existing session authorization.

## Operation selection
Resolve the workflow and requested operation. Review reports findings without edits. Revision copies a published definition into its draft; fork uses a new ID and records provenance in prose. Publication-only requests do not reopen settled interviews.

## Minimum required context
Read the existing definition and [format reference](references/protocol.md). For new or revised authoring, load [onboarding](references/onboarding.md) and [starter template](assets/WORKFLOW.md). Inspect available context, ask short gap questions, and keep drafting independent sections while awaiting answers. Do not require user-prepared files. Resolve goals, input collection, deliverables, acceptance, interaction policy, work boundaries, dependencies, capabilities and retry bounds. Approval steps are explicit authoring choices; do not insert a generic approval gate.

## Command sequence
Run `uv run /absolute/path/to/this/skill/scripts/workflow.py` with the commands below. Relative data paths resolve from the user's repository.

1. Use `inspect FILE` for structure and requirements. Draft in `workflows/<id>/draft/WORKFLOW.md` with YAML front matter containing the complete steps tree and stable-ID prose headings.
2. Write Task, Inputs, Outputs, Acceptance for each step; add Fallback for optional skills, Approval scope for chosen gates, and Retry policy when applicable. Use exact subworkflow pins and explicit branch joins; bound every iteration.
3. Run `validate FILE --root .`. Resolve diagnostics, then assess prose by walking branches, joins, loop exhaustion, missing capabilities and recovery. Mechanical validation does not judge actual consent or semantic quality.
4. If publication was requested, run `publish FILE --root . --version X.Y.Z` and `verify-release ID X.Y.Z --root .`. Never reuse a version or edit published definitions. Otherwise report the draft path.

## Completion and reporting
Report what changed, intended execution behavior, deliverables and any unresolved gaps. Publication requires resolved requirements and policy. Use major versions for incompatible behavior/inputs, minor for compatible additions, patch for corrections. Project defaults customize inputs; changed step logic requires a new release or fork. Each installed skill is self-contained and must never import from its sibling or the source checkout.
