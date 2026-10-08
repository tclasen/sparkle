# Contributing

Start with [README.md](README.md) for the product and [INTENT.md](INTENT.md) for its purpose and requirements. Keep changes focused and explain changes to the workflow contract or user-visible behavior.

## Set up

Use a local checkout with Python 3.11 or later and uv installed. Node.js and npx are also needed for installation verification. There is no application server to start. Python scripts declare their dependencies inline for uv.

Run the baseline checks from the repository root:

```sh
python3 scripts/bundle.py --check
uv run tests/test_workflows.py
```

## Find the right source

| Location | Edit here for |
| --- | --- |
| `shared/scripts/workflow.py` | Validation, publication, snapshots, and run-management commands |
| `shared/references/` | Shared format, onboarding, and execution protocols |
| `shared/assets/` | Workflow, project, environment, and result templates |
| `skills/define-workflow/SKILL.md` | Authoring skill entry instructions |
| `skills/execute-workflow/SKILL.md` | Execution skill entry instructions |
| `examples/` | Example workflows and agent walkthroughs |
| `tests/test_workflows.py` | Behavioral checks of the public CLI |
| `tests/verify_install.py` | Real installation and standalone skill verification |
| `scripts/bundle.py` | Deterministic packaging of shared resources |

The `scripts/`, `references/`, and `assets/` directories inside each skill are generated copies. Edit their canonical files in `shared/`, then regenerate both bundles:

```sh
python3 scripts/bundle.py
```

Include the shared changes and both generated bundles in the same contribution. The two `SKILL.md` entry files are maintained directly and are not generated.

## Make a change

Recursively decompose each requested change into as many small, independently verifiable units as possible, and work through them in dependency order. For each unit: make the change easy to make with focused preparation, make the change, verify it locally, and commit it using Conventional Commits. Independently verifiable preparatory refactors are separate units following the same sequence. Stage only files or hunks belonging to the unit.

1. Identify the expected behavior and read the relevant protocol and tests. For a bug, capture the concrete trigger and expected outcome.
2. Implement the smallest coherent change. Keep installed skills independent of `shared/`, each other, and the source checkout.
3. Add or update behavioral tests for changed validation, state transitions, snapshot isolation, or recovery. Exercise the public CLI and observable outcomes; do not hand-edit canonical run state to simulate valid operations.
4. Update affected protocol text, templates, examples, and README instructions. If purpose, requirements, or scope change, update `INTENT.md` in the same contribution and explain the reason.
5. Regenerate bundles when shared resources change, then run the relevant checks.

Use temporary repositories for experiments and test runs. Keep generated project data, real credentials, and private user artifacts out of contributions. Examples and walkthroughs use simulated evidence; do not describe them as live execution results.

## Verify

```sh
python3 scripts/bundle.py --check
uv run tests/test_workflows.py
```

The behavioral suite covers structure, branching and joins, approvals, iteration bounds, composition, capabilities, snapshots, ownership, revisions, evidence, recovery, examples, and bundle consistency.

For changes to packaging, dependencies, skill resources, or the execution interface, also run:

```sh
uv run tests/verify_install.py
```

This check installs both skills through the pinned skills CLI in a temporary project, compares their resources, then isolates and exercises each skill independently. It needs Node/npx and network access or populated npm/uv caches; it prints the CLI version and commands for reproducibility.

For root documentation-only changes, check relative links and command accuracy and run the bundle freshness check. No new tests are needed for prose alone. Report checks that could not run and their actual blockers; do not claim a pass from inspection.

## Diagnose environment failures accurately

A sandbox can permit source edits while denying Git metadata writes, the credential keychain, dependency caches, or network access. A failure to lock a branch ref, initialize uv's cache, resolve a package host, or authenticate with `gh` may therefore be an execution-environment restriction. Inspect the specific error and retry through the environment's authorized permission mechanism when appropriate. Do not immediately replace credentials, change remotes, weaken repository rules, or report a test failure as a product defect. Avoid printing credentials while diagnosing access.

If only the cache location is unwritable, a writable temporary `UV_CACHE_DIR` or `npm_config_cache` can help. A fresh cache still needs dependency downloads; relocating it does not solve DNS or network restrictions. The installation check invokes the pinned skills CLI and uv in temporary projects, so it needs either usable dependency caches or network access. Preserve the actual failure output and distinguish a blocked check from a passing one. Run dependent verification sequentially after edits settle so results describe the final files; avoid overlapping redundant suites.

Use the public CLI with temporary fixtures to test run transitions, ownership, revisions and recovery. Simulated ticket observations demonstrate local enforcement and its limits, including the race where two peers begin before observing one another. They do not establish provider consistency, write durability, idempotency, or real authorization. Live provider checks need an explicitly designated test ticket. Installed-resource checks must exercise each skill alone; success from the source checkout cannot prove standalone portability.

Keep repository delivery and environment guidance here and in `AGENTS.md`. Product coordination behavior belongs in the [shared coordination reference](shared/references/coordination.md), with simulated scenarios in [the walkthroughs](examples/WALKTHROUGHS.md). Root documentation changes alone do not require regenerated skill bundles or new behavioral tests; shared resources do. This keeps contributor-specific procedures out of installed user workflows.

## Deliver to main

Use Conventional Commit messages for each unit, such as `fix: preserve run evidence` or `docs: clarify installation`. Explain the problem, resulting behavior, and validation performed in commits or pull requests. Call out changes to document formats, commands, approval semantics, or recovery behavior, including compatibility impact. Include updated generated bundles where applicable.

Delivery uses a pull request to `main` and **merge commits**. Preserve the individual signed unit commits and their hashes; the PR adds one integration commit. Squash and rebase merging are not allowed. GitHub rebase merging rewrites commits without preserving their signatures and cannot satisfy required signed commits. Do not force-push, overwrite unrelated work, or substitute a direct push to `main` when a pull request merge fails.

### Inspect the target before delivery

The default branch is `main`. The earlier default of `docs/change-delivery-workflow` belonged to the previous repository and is historical; its cause was not established. Recheck the actual configuration below after repository recreation or settings changes.

Fetch `upstream` and check the actual refs, repository settings, and effective rules. A ruleset's name does not determine its target. A ruleset named `main` that includes `~DEFAULT_BRANCH` protects whichever branch is currently the default, which may be a feature branch. A successful push or a clean PR does not prove `main` is protected. Repository merge settings and a ruleset's allowed merge methods must both permit merge commits. Required linear history must be off because it prohibits merge commits.

```sh
git fetch upstream
git ls-remote --heads upstream
gh api repos/tclasen/sparkle --jq '{default_branch,allow_merge_commit,allow_squash_merge,allow_rebase_merge}'
gh api repos/tclasen/sparkle/rulesets
gh api repos/tclasen/sparkle/rules/branches/main
```

Inspect an individual ruleset with `gh api repos/tclasen/sparkle/rulesets/RULESET_ID` when its conditions or allowed methods need checking. The classic branch-protection endpoint can return 404 while a ruleset exists; check rulesets and effective branch rules before concluding that protection is absent. If access is denied, report that uncertainty rather than treating it as an empty rule set.

If PR creation reports missing head/base SHAs or no commits, verify remote branch existence and the intended base before retrying. If `main` is missing or settings conflict with the required merge-commit method, report the concrete configuration blocker. Do not create a replacement base, change repository settings, or bypass protections as an incidental delivery workaround.

For maintainers, the intended configuration is default branch `main`, effective protection of `refs/heads/main`, and merge commits as the only allowed PR merge method. Disable squash/rebase merging and required linear history. Keep required signed commits, pull requests, resolved review threads, deletion protection and force-push protection. Choose human-review requirements deliberately: zero approvals permits autonomous delivery, while requiring an approval introduces a human review step. If signed commits are required, verify contributor signing support. Required checks need actual CI jobs; local test success does not create a GitHub status check. An empty check list means no checks were reported, not that CI passed.

### Push, merge, and synchronize

When all units pass their local checks, push the feature branch to `upstream` ([tclasen/sparkle](https://github.com/tclasen/sparkle)) and open a PR with explicit `--base main`. Write multiline PR text to a file and pass `--body-file` so shell quoting cannot change the description. Inspect the PR's current head, checks and review requirements, then merge only the reviewed head:

```sh
gh pr view PR_NUMBER --repo tclasen/sparkle --json headRefOid,mergeStateStatus,reviewDecision,statusCheckRollup
gh pr merge PR_NUMBER --repo tclasen/sparkle --merge --match-head-commit REVIEWED_HEAD_SHA
```

Replace the placeholders with the actual PR number and reviewed head SHA. Satisfy required checks and reviews; do not use an administrative bypass. If the head changes, inspect the new changes and relevant validation before merging. A merge error or lost response requires inspecting PR state and remote refs before retrying or claiming completion.

After confirming the PR merged, switch to local `main`, run `git pull --ff-only upstream main`, and compare `git rev-parse HEAD` with `git ls-remote upstream refs/heads/main`. Inspect the delivered unit commits and requested content, and check `git status --short`. If local `main` diverged, preserve that work and resolve the divergence without a destructive reset. Work is complete only when the changes are in remote `main` and pulled down locally. Report access, review, configuration, or verification blockers explicitly; a pushed branch or open PR is not completed delivery.

Do not change the published workflow versioning contract incidentally: released definitions are never overwritten, and composed workflows use exact versions. The current product has no old-format readers or migration interface. Proposals to change that scope should update the intent and protocol explicitly.
