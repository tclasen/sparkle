# Working on this repository

These instructions apply to AI agents contributing to this project. They describe repository development; the installed skills' own instructions govern authoring and executing workflows in user repositories.

## Understand the task

- Read `README.md`, `INTENT.md`, and `CONTRIBUTING.md` before making changes. Read the relevant shared protocol and tests for the area you touch.
- Inspect existing code and session context before asking questions. Resolve routine implementation choices yourself; ask when a missing requirement materially affects behavior or scope, and continue independent work while waiting.
- Complete authorized work without adding generic approval gates. Preserve actual user authorization and concrete approval scopes. Repository commits, pushes, and merges are authorized by the delivery workflow below; this does not authorize publishing workflow releases or unrelated external actions.
- Preserve unrelated user changes. Keep edits focused and report material limitations candidly.

## Deliver changes in small units

- For every requested change, recursively decompose the task into as many small, coherent units of work as possible. Continue splitting until each unit can be implemented, verified locally, and committed independently. Execute units in dependency order.
- For each unit, follow this sequence:
  1. Make the change easy to make: inspect the relevant code and tests and prepare the smallest necessary setup or refactor. Treat independently verifiable preparatory changes as their own units using this same sequence.
  2. Make the change, keeping it focused on the unit's purpose.
  3. Verify it locally using the checks appropriate to the change in `CONTRIBUTING.md`. Resolve failures before committing; report genuine blockers without claiming success.
  4. Commit the unit using Conventional Commits, such as `docs: clarify delivery workflow` or `fix: preserve run evidence`. Stage only the unit's files or hunks.
- Before delivery, inspect remote refs, repository merge settings, and effective rules for `main` using the procedure in `CONTRIBUTING.md`. Ruleset names and the default branch can differ from their intended target. Report missing branches or conflicting settings; do not change repository configuration as an incidental workaround.
- Once all units are complete, push the feature branch to `upstream` (`tclasen/sparkle`), open a PR explicitly targeting `main`, and use a merge commit, satisfying required checks and branch protections. Preserve the individual signed unit commits and their hashes. Do not squash, rebase-merge, force-push, overwrite unrelated work, or fall back to a direct push to `main`. Required linear history must be disabled for this policy; required signatures remain enabled. Pin the merge to the reviewed PR head and inspect remote state after uncertain merge responses.
- Pull remote `main` into local `main` with a fast-forward pull, and verify that local `HEAD` matches the remote `main` commit and that the requested changes are present. A change is complete only when it is in remote `main` and pulled down locally.
- Carry this delivery through without asking for routine permission again. If access, required review, or a failed check blocks delivery, state what remains incomplete and the concrete blocker; a local commit, pushed branch, or open pull request alone is not completion.

## Edit canonical sources

- Change shared implementation, references, and templates under `shared/`. Do not edit generated copies under `skills/*/{scripts,references,assets}` directly.
- After shared changes, run `python3 scripts/bundle.py` and include both refreshed bundles.
- Edit the two `skills/*/SKILL.md` entry files directly when their distinct instructions need to change.
- Each installed skill must work alone, without imports or resources from a sibling skill or the source checkout.
- Keep behavior, protocol documentation, templates, examples, and tests consistent. Update `INTENT.md` when intended requirements or boundaries change; distinguish proposals from implemented behavior.

## Preserve the product contract

- Agents interpret prose, assess acceptance criteria, and verify consent. Python validates structure and maintains records; successful validation is not proof of quality, consent, or an external outcome.
- Preserve safe YAML parsing, strict metadata validation, exact composition pins, release hash checks, and per-run snapshots.
- Preserve ownership, revision, locking, transition-history, and evidence checks. Use the helper's public commands for run mutations; never bypass them by editing `state.json` or replacing whole-state records.
- Preserve attempts, iteration bounds, artifacts, and recovery history. Inspect and reconcile uncertain external effects before retrying. Cancellation is not rollback.
- Do not overwrite published workflows, rewrite frozen run context, or reopen terminal runs. Changed workflow behavior requires a new release or fork; changed run inputs require a new run.
- Keep conversational onboarding: use existing context, ask focused gap questions, and have the agent prepare files. Do not invent answers, approval evidence, or tool availability.
- Serial foreground coordination is the default. Do not introduce a scheduler, provider-specific runtime, or mandatory delegation as an incidental implementation change.

## Verify and report

- Follow `CONTRIBUTING.md` for check selection. Run `python3 scripts/bundle.py --check` and, for implementation changes, `uv run tests/test_workflows.py`.
- Run `uv run tests/verify_install.py` when changing packaging, dependencies, skill resources, or the execution interface. Report environmental blockers accurately.
- Add meaningful behavioral coverage for changed contracts; avoid tests that merely duplicate implementation or test prose edits.
- Use temporary directories for fixtures and experiments. Do not add real user run data or credentials to the repository.
- Diagnose sandbox, cache, network, and credential-access failures using `CONTRIBUTING.md` before attributing them to code or invalid credentials. Use authorized execution permissions; do not expose secrets or change security settings to make checks pass.
- Summarize what changed, why, checks performed and their outcomes, and unresolved issues. Do not present simulated example evidence as observed real-world results.
