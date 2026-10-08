# Using sparkle

Turn a conversational description of repeatable work into a versioned procedure that an AI agent can carry out across projects, with recorded progress and evidence.

sparkle provides portable natural-language workflows through two independently installable Agent Skills. The upstream repository is [tclasen/sparkle](https://github.com/tclasen/sparkle).

- **define-workflow** helps you draft, review, revise, fork, and explicitly publish workflows.
- **execute-workflow** helps you create projects, run published workflows, inspect progress, recover interrupted work, retry steps, and cancel runs.

Workflows combine Markdown instructions with YAML metadata describing tasks, dependencies, decisions, approval gates, bounded iteration, and nested workflows. Agents interpret instructions and judge results. A Python helper validates structure and maintains durable repository-local records. There is no background scheduler, service, or automatic rollback.

## Install

You need an agent that supports Agent Skills, Python 3.11 or later, [uv](https://docs.astral.sh/uv/), and Node.js with `npx` for installation. The helper declares its PyYAML dependency inline; uv installs it when needed.

From your project directory, install with the [skills.sh CLI](https://skills.sh/docs/cli):

```sh
npx skills add tclasen/sparkle --skill define-workflow execute-workflow
```

Choose your agent when prompted. This follows development on main. To pin a release, use the tagged URL shown in that [release's installation command](https://github.com/tclasen/sparkle/releases). The [official CLI source-format documentation](https://github.com/vercel-labs/skills#source-formats) explains GitHub tree URLs.

Each skill includes its own instructions, helper, references, and templates; neither needs its sibling at runtime.

## Use it conversationally

### 1. Describe a workflow

> Help me set up a research workflow that turns a topic into a sourced report. Call it research-to-deliverable.

The agent reads available context and asks short questions about goals, inputs, deliverables, acceptance criteria, and boundaries. It also asks how to handle uncertainty during execution: when to ask you, apply agreed defaults, or stop with a blocker. You do not need to prepare templates or JSON files yourself.

The agent saves a draft and explains its behavior. Ask it to review or revise the draft until it describes the procedure you want.

### 2. Publish a version

> Publish research-to-deliverable as 1.0.0.

Publication requires an explicit request. Published versions are not edited in place. Changing step logic requires a new release or a fork; project context and input defaults let you reuse the same workflow for different work.

### 3. Create a project and start a run

> Create project launch-study and run research-to-deliverable to research the audience for our new product.

The agent collects missing context and prepares the files. Reusable answers become project context or defaults; answers specific to this run remain separate. It checks available capabilities and summarizes readiness before starting. New runs use the highest published numeric version unless you specify one.

Each run freezes its workflow definitions, composed versions, project context, inputs, and capability inventory. The agent checkpoints work with assessments and local evidence, following the workflow's interaction policy and concrete approval gates.

### 4. Inspect or continue work

- “Show the status of the launch-study run.”
- “Resume the interrupted run.”
- “Retry the failed step.”
- “Cancel this run.”

Recovery preserves prior attempts and inspects uncertain external actions before retrying. Changed definitions or inputs require a new run. Cancellation preserves artifacts and history; it does not undo external actions.

## Coordinate independent peers

Agents on separate machines can optionally use existing ticket tools to exchange advisory claims, assessed dependencies, results and handoffs. Each ticket represents one work unit with its own local run and isolated work area. See the [peer coordination protocol](../shared/references/coordination.md) and [simulated walkthrough](../examples/WALKTHROUGHS.md). Claims are best effort: simultaneous peers can still duplicate work before observing a conflict.

## Where your work lives

Files are created in the repository where you use the skills:

```text
workflows/<id>/draft/WORKFLOW.md
workflows/<id>/versions/<version>/{WORKFLOW.md,release.json}
projects/<id>/PROJECT.md
projects/<id>/{inputs,outputs}/
projects/<id>/runs/<run-id>/
  state.json
  journal.md
  owner.json                 # while coordinated
  project-snapshot.md
  artifacts/
  workflow-snapshot/workflows/<id>/versions/<version>/
```

Hashes detect changes to published or snapshotted definitions; they do not enforce filesystem immutability or guarantee identical agent judgments. Referenced external file contents must be captured separately when needed. Structural checks cannot establish result quality, actual user consent, or external action outcomes.

## Examples and reference

- [Minimal linear workflow](../examples/minimal-linear/WORKFLOW.md): a small procedure without an approval gate.
- [Research to deliverable](../examples/research-to-deliverable/WORKFLOW.md): branching, a join, optional skill fallback, bounded refinement, and approval.
- [Software feature delivery](../examples/software-feature/WORKFLOW.md): required skills and an exact-version [quality-check](../examples/software-feature/quality-check.md) subworkflow. Publish quality-check first.
- [Agent walkthroughs](../examples/WALKTHROUGHS.md): simulated authoring, execution, approval, and recovery scenarios.
- [Format and CLI reference](../skills/execute-workflow/references/protocol.md): document schemas, commands, and transition rules.

## Develop this project

Read [CONTRIBUTING.md](../CONTRIBUTING.md) for setup, changes, and verification. [INTENT.md](../INTENT.md) records the product purpose, requirements, and non-goals. [AGENTS.md](../AGENTS.md) guides AI agents working on this repository.

Canonical helper code, references, and templates live in `shared/`; `scripts/bundle.py` copies them into both distributable skills. The main checks are:

```sh
python3 scripts/bundle.py --check
uv run tests/test_workflows.py
uv run tests/verify_install.py
```

The installation check uses the actual skills CLI and requires Node/npx plus network access or populated dependency caches. See the contribution guide for when each check is needed.
