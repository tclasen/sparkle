# Project release policy

sparkle starts at **v0.1.0**. Project releases use [Semantic Versioning](https://semver.org/spec/v2.0.0.html) and [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/). They are distinct from workflow definitions published by the helper: those keep their own explicit publication, immutable versions and exact composition pins.

## Before 1.0

Every 0.x release may break compatibility. Backwards compatibility and regression testing are not release requirements. Current structural validity, complete skill bundles, successful installation, and correctness of release tooling still matter. This policy does not authorize invalid packages or changes to frozen user run records.

The first release is exactly `v0.1.0`. Thereafter, `feat` and breaking changes (`!` or a `BREAKING CHANGE:` / `BREAKING-CHANGE:` footer) increment the minor version. `fix` and `perf` increment the patch version. Other commit types do not independently trigger a release, but their changes appear in the next release's notes. The highest applicable bump wins across all commits since the previous release. Merge commits are excluded; the individual commits in a PR are validated and analyzed.

## Entering stable releases

Set `stable` to `true` in [release.json](../release.json) through a reviewed PR to opt into **1.0.0**. Breaking changes alone never graduate a 0.x project to 1.0. Once stable, do not turn this setting off. At and after 1.0, breaking changes increment the major version, features the minor version, and fixes/performance changes the patch version.

The stable public contract includes the documented helper CLI, workflow/project metadata, run records and recovery behavior, and standalone skill resources. Starting with 1.0.0, changes must assess backwards compatibility against that contract and run the behavioral regression suite. The 1.0 milestone must define supported compatibility boundaries and add fixtures for the stable formats; passing a version-number check alone does not prove compatibility. Existing 0.x formats do not acquire a retroactive support promise.

Published versions, tags and assets must never be replaced. Correct mistakes in a new release. A retry may complete an interrupted publication only when the existing target and content match exactly.
