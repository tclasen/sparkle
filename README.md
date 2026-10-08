# sparkle

sparkle turns repeatable work into versioned, natural-language workflows that AI agents can carry out with recorded progress and evidence.

It provides two independent skills:

- **define-workflow** helps you create, review, revise, and publish workflows.
- **execute-workflow** helps you run them, inspect progress, and recover interrupted work.

## Install

Use the [skills.sh CLI](https://skills.sh/docs/cli) from your project directory. You need Node.js, Python 3.11+, and [uv](https://docs.astral.sh/uv/).

```sh
npx skills add tclasen/sparkle --skill define-workflow execute-workflow
```

Choose your agent when prompted. This installs the current development version from main.

To pin a release, use its version tag in a GitHub tree URL. See the [official skills CLI source-format documentation](https://github.com/vercel-labs/skills#source-formats); each [sparkle release](https://github.com/tclasen/sparkle/releases) provides the exact pinned command. Before 1.0, releases may introduce breaking changes.

## Use

Ask your agent to:

1. “Help me create a research workflow that turns a topic into a sourced report.”
2. “Publish that workflow as version 1.0.0.”
3. “Create a project and run the workflow to research our product's audience.”
4. “Show the run's status,” “Resume the interrupted run,” or “Cancel this run.”

The agent asks for missing context, prepares the files, and records progress. Workflow publication is explicit; each run keeps its original inputs and instructions.

See [the usage guide](docs/GUIDE.md) for examples and recovery details, or [Contributing](CONTRIBUTING.md) to work on sparkle itself.

Proposed skill changes use [paired usefulness evaluations](docs/EVALUATIONS.md) across two models and two coding harnesses. See [evaluation setup](docs/EVAL_CONFIGURATION.md) for configuration and validation status.

The [initial 64-run screening](docs/evals/2026-10-08-screening/README.md) records objective outcomes for both skills and the pre-authored workflows. Its one-repeat results do not establish net benefit or a proven catalog.
