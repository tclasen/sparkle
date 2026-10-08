# Project release policy

sparkle starts at **v0.1.0**. Project releases use [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). They are distinct from workflow definitions published by the helper: those keep their own explicit publication, immutable versions and exact composition pins.

## Before 1.0

Every 0.x release may break compatibility. Backwards compatibility and regression testing are not release requirements. Current structural validity, complete skill bundles, successful installation, and correctness of release tooling still matter. This policy does not authorize invalid packages or changes to frozen user run records.

The first release is exactly `v0.1.0`. Thereafter, `feat` and breaking changes (`!` or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer) increment the minor version. `fix` and `perf` increment the patch version. Other commit types do not independently trigger a release, but their changes appear in the next release's notes. The highest applicable bump wins across all commits since the previous release. Merge commits are excluded; the individual commits in a PR are validated and analyzed.

## Entering stable releases

Set `stable` to `true` in [release.json](../release.json) through a reviewed PR to opt into **1.0.0**. Breaking changes alone never graduate a 0.x project to 1.0. Once stable, do not turn this setting off. At and after 1.0, breaking changes increment the major version, features the minor version, and fixes/performance changes the patch version.

The stable public contract includes the documented helper CLI, workflow/project metadata, run records and recovery behavior, and standalone skill resources. Starting with 1.0.0, changes must assess backwards compatibility against that contract and run the behavioral regression suite. The 1.0 milestone must define supported compatibility boundaries and add fixtures for the stable formats; passing a version-number check alone does not prove compatibility. Existing 0.x formats do not acquire a retroactive support promise.

Published versions, tags and assets must never be replaced. Correct mistakes in a new release. A retry may complete an interrupted publication only when the existing target and content match exactly.

## Local commit and version checks

Use Python 3.11+ and a full Git checkout with all release tags. Project release tags have the form `vMAJOR.MINOR.PATCH`; prerelease suffixes and build metadata are not used by this release channel. Other tags may exist, but names starting with `v` are reserved for project releases. Versions are ordered numerically and checked against their commit history, not inferred from tag creation dates.

```sh
git fetch upstream --tags
python3 scripts/release.py lint --base upstream/main
python3 scripts/release.py plan
python3 tests/test_releases.py
```

Planning reads committed `release.json` at HEAD. Commit local changes before previewing the exact release. Accepted commit types are `feat`, `fix`, `perf`, `docs`, `refactor`, `style`, `test`, `build`, `ci`, `chore`, and `revert`, with optional scope and `!`. Bodies follow a blank line; breaking-change footers need explanations. A revert does not automatically cancel another commit's bump: use `fix` or a breaking marker when the revert itself needs a release. Only actual merge commits are exempt from message linting. PR titles are not used to calculate versions.

`plan` is read-only and reports no version for a documentation-only interval after the initial release. Planning on an existing release tag reproduces that version for publication recovery. Invalid versions, incorrect bumps, divergent release tags and shallow history fail closed. The helper validates structure and declared change type; contributors still assess whether a change is actually breaking.

## Reproducible release packages

```sh
python3 scripts/release.py build --output /tmp/sparkle-release-preview
```

Use a fresh output directory and a clean tracked working tree. Builds read committed Git blobs, not untracked files. Each release contains two standalone skill ZIPs, `RELEASE_NOTES.md`, a cumulative `CHANGELOG.md`, `release.json` identifying the source commit, and `SHA256SUMS.json`. ZIP entries use fixed timestamps and no compression so reruns produce identical bytes across supported systems. Each ZIP contains a skill with a `RELEASE.json` receipt. Skill contents otherwise match the tagged source exactly.

Git tags and release receipts are the authoritative project version; source skills omit a version field so a skills.sh installation cannot carry stale metadata. The automation does not create version-bump or changelog commits on protected main. Cumulative changelogs are generated release assets, and GitHub release bodies contain the release-specific notes. This avoids needing bot commits, signing keys, or a branch-protection bypass for release bookkeeping.

## Installation through skills.sh

The primary installation path is `npx skills add https://github.com/tclasen/sparkle/tree/vX.Y.Z --skill define-workflow execute-workflow`. Each release note includes the exact command. Use a published tag, not the default branch, to select a release. `npx skills add tclasen/sparkle` tracks development on main; it does not select the latest semantic version. No npm package or separate skills.sh upload is required.

Before publishing, verify local installation with `uv run tests/verify_install.py --smoke-only`. After a tag exists, verify the actual documented path from a checkout of that tag with `uv run tests/verify_install.py --source https://github.com/tclasen/sparkle/tree/vX.Y.Z --smoke-only`. Both commands use the pinned skills CLI, compare every installed resource with the expected checkout, isolate each skill, and validate its starter workflow. Omit `--smoke-only` for the complete behavioral installation walkthrough, required at/after 1.0.

`python3 tests/verify_tag_install.py` exercises that same GitHub tree/tag URL before pushing. It rewrites only the test repository's Git clone URL to a temporary local repository, tags valid skills, then changes main to invalid sentinel content. Successful installation therefore proves tag selection and resource preservation without creating a real tag. It does not prove GitHub availability; the live tagged installation is checked during publication.
