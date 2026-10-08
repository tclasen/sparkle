# GitHub Actions workflows

[Validate and release](../.github/workflows/validate-release.yml) uses the same Python entry points as local verification. These Mermaid diagrams render directly on GitHub. Actions provide checkout, pinned tool setup, event selection, credentials and concurrency; project logic lives in locally runnable scripts.

## Validation

```mermaid
flowchart TD
    A[PR to main, push to main, or manual run] --> B[Full checkout with tags]
    B --> C[Validate Conventional Commits and SemVer history]
    C --> D[Check syntax, links, Actions YAML, and bundle freshness]
    D --> E[Test release planning, packaging, and recovery]
    E --> F[Install both skills with pinned skills CLI]
    F --> G[Verify tagged URL against local Git fixture]
    G --> H{Stable policy enabled?}
    H -->|No: before 1.0| I[No compatibility or regression gate]
    H -->|Yes: 1.0 and later| J[Run behavioral regression and full installation walkthrough]
    I --> K[Build release preview and verify checksums when releasable]
    J --> K
    K --> L[validation check passes]
```

Local equivalent, after committing changes and fetching main/tags:

```sh
python3 scripts/check.py --base upstream/main
```

Omit `--base` to lint all non-merge commits, as the main workflow does. Install Python 3.11+, Node.js 24, uv 0.12.23, Go 1.26+, Git, and the GitHub CLI. The scripts pin skills CLI 1.7.1 and actionlint 1.7.12. Actionlint's optional shellcheck/pyflakes integrations are explicitly disabled in both local and CI runs so installed host utilities cannot change the checks. Python source syntax is checked separately. npm, uv and Go need network access or populated caches.

Before 1.0 the release-tool tests establish correctness of the release machinery; they are not a backwards-compatibility or product-regression requirement. At/after 1.0 the existing behavioral suite and full installation walkthrough become mandatory. Contributors must also assess public-contract compatibility; a machine cannot infer whether a commit's declared type is truthful.

## Version selection

```mermaid
flowchart TD
    A[Validated commits since last release] --> B{Any existing release?}
    B -->|No| C[v0.1.0]
    B -->|Yes| D{Promote stable from false to true?}
    D -->|Yes, previous major is zero| E[v1.0.0]
    D -->|No| F{Breaking change?}
    F -->|Yes, major is zero| G[Minor bump within 0.x]
    F -->|Yes, major is one or higher| H[Major bump]
    F -->|No| I{Feature?}
    I -->|Yes| J[Minor bump]
    I -->|No| K{Fix or performance change?}
    K -->|Yes| L[Patch bump]
    K -->|No| M[No new release]
```

Local equivalent: `python3 scripts/release.py plan`. A reviewed `release.json` change opts into 1.0. No breaking marker can promote 0.x by itself.

## Publication and recovery

```mermaid
flowchart TD
    A[validation passed] --> B{Push or manual run on main?}
    B -->|No: PR| C[Stop without write credentials]
    B -->|Yes| D[Inspect main signature, tags, and prior releases]
    D --> E{Releasable changes or matching retry?}
    E -->|No| F[No publication]
    E -->|Yes| G[Build deterministic ZIPs, notes, changelog, and checksums]
    G --> H[Create or inspect version tag and draft release]
    H --> I[Install from actual GitHub tag URL with skills CLI]
    I --> J[Upload missing assets and verify all asset bytes]
    J --> K[Publish completed draft]
    H -->|Conflicting existing content| X[Stop for inspection; never overwrite]
    I -->|Failure| Y[Keep tag and draft for recovery]
    J -->|Lost response or failure| Y
    Y --> Z[Retry original commit; inspect receipts first]
    Z --> H
```

Local preview: `python3 scripts/publish.py --output /tmp/sparkle-preview` (fresh directory). Publication uses that same command with `--execute` and GitHub authentication. The real tag URL cannot be verified before the tag exists; the local fixture exercises tag selection beforehand, and the publication job checks the live provider before announcing the release. See [recovery instructions](RELEASING.md).

The workflow serializes main runs and never cancels a running publication. GitHub may replace queued pending runs; the next run considers every unreleased commit. If main advances during a job, publication stops rather than tagging an outdated checkout. Rerun on current main, or use the documented original-commit resume procedure when a tag/draft already exists. No `pull_request_target` event or PR write token is used.

## Repository configuration

Keep the signed merge-commit rules documented in [Contributing](../CONTRIBUTING.md). Once this workflow has run successfully, require the **validation** status check on main. Do not require **publication** before merging: it runs only after a merge. GitHub Actions must be enabled; only the publication job requests `contents: write`. No personal token, bot signing key, or protected-branch bypass is needed. Tag rules must allow the Actions token to create new `v*` tags; never allow release automation to move existing tags. A tag-protection policy that denies creation will block publication and must be configured by a maintainer.

The automation makes no source commits, opens no release PRs, and needs no new workflow triggered by its own tags. Generated notes and the cumulative changelog are attached to releases. Installing from a published tag selects exactly that source version; the unqualified repository install selects main.
