# Evaluation configuration and preflight

Use this guide with [the evaluation policy](EVALUATIONS.md). The four cells select the same two model identities explicitly; Codex and Pi use their native tools and provider adapters. A configuration probe establishes inference and tool connectivity, not useful skill outcomes.

## Pinned setup

The 2026-10-08 preflight used macOS arm64, Codex CLI **0.162.0** (`@openai/codex`), Pi coding harness **1.0.4** (`@earendil-works/pi-coding-agent`), Ollama **0.40.1**, and existing ChatGPT/OpenAI subscription OAuth in each harness. Pi's installed executable was `/opt/homebrew/bin/pi`. Keep these versions fixed within a comparison; newer versions require a fresh preflight. Pi 1.1.0 was available but was not used in these observations.

Codex 0.162.0 was the newest npm release when checked. The host Homebrew Codex remained 0.161.0 because this account could not write Homebrew's lock directory. Validation instead used an isolated npm installation of 0.162.0; the previously created Docker sandbox also has 0.162.0. No Homebrew permissions were changed.

Install reproducible harness executables in a separate temporary directory rather than relying on the shell's global executable:

```sh
eval_tools=$(mktemp -d /private/tmp/sparkle-eval-tools.XXXXXX)
npm install --prefix "$eval_tools" @openai/codex@0.162.0 @earendil-works/pi-coding-agent@1.0.4
eval_codex="$eval_tools/node_modules/.bin/codex"
eval_pi="$eval_tools/node_modules/.bin/pi"
"$eval_codex" --version
"$eval_pi" --version
```

Use a task-specific `npm_config_cache` or `UV_CACHE_DIR` if the normal cache is unwritable. Downloads still need authorized network access. Keep runtime files and raw evidence outside this checkout.

## Providers and authentication

| Cell | Requested model | Provider and wire format | Authentication |
| --- | --- | --- | --- |
| Codex / local | `gpt-oss:120b` | `ollama-local`, Ollama `/v1/responses` | No provider credential |
| Codex / Luna | `gpt-6-luna` | Built-in `openai`, subscription route | Codex ChatGPT OAuth |
| Pi / local | `gpt-oss:120b` | Custom `ollama`, `openai-completions` | Dummy `ollama` key |
| Pi / Luna | `gpt-6-luna` | Built-in `openai-codex`, `openai-codex-responses` | Pi subscription OAuth |

Authenticate independently if needed: `codex login` for Codex; start Pi and use `/login openai-codex` for Pi. `codex login status` and `pi auth check --provider openai-codex --model gpt-6-luna --json` report readiness without printing tokens. Never use Pi's `--credentials` or credential-printing commands in evidence capture. The preflight removed `OPENAI_API_KEY` from the child processes so the Luna cells used existing subscription authentication. Do not substitute `--provider openai` in Pi: that selects its API-key provider.

The host endpoint is `http://127.0.0.1:11434`; a Docker sandbox reaches the same Mac service through `http://host.docker.internal:11434`. Verify `/api/tags` and `/api/ps`. The model needs approximately 65 GB of weights; the tested Mac has 128 GiB of RAM. Initial loading can take minutes, and local multi-turn Codex requests can be considerably slower than a greeting. Keep cold-start status and timeouts in the run record.

The current host's `/api/tags` advertises two `gpt-oss:120b` entries with different runners/digests, plus a `llamacpp:` alias. The observed loaded runner during this preflight was `llamacpp`, digest `ad84bf7720de3aac13b8f07008047c85ff5c277721a648dbf51517453a0331f6`, with context length 131072. The other advertised digest was `7da0a7eefc4c5acd46742134ef1c05ff635ea3840d8ec8580f303b09f3641d5a`. Record both advertised and loaded metadata per batch, and investigate any routing/digest change before treating paired results as comparable. The earlier sandbox greeting used a different digest; it is a separate observation. Hosted Luna did not expose an immutable weight digest; record the requested/returned model ID and date rather than inventing a pin.

The checked-in [Codex configuration](eval-config/codex-ollama.toml) and [Pi model configuration](eval-config/pi-models.json) contain no secrets. Pi's zero local-model token prices are catalog bookkeeping, not a claim that local compute is free. Its hosted catalog cost estimates are not subscription billing evidence.

For Pi, keep the existing global model configuration intact. Put the provided JSON in a separate agent configuration directory, and reference the already authenticated host file without printing or committing it:

```sh
eval_repo=$(pwd)  # Run this setup from the sparkle checkout.
eval_pi_dir=$(mktemp -d /private/tmp/sparkle-eval-pi.XXXXXX)
cp "$eval_repo/docs/eval-config/pi-models.json" "$eval_pi_dir/models.json"
ln -s "$HOME/.pi/agent/auth.json" "$eval_pi_dir/auth.json"
```

Pi refreshes that existing private OAuth store when necessary. Do not run two processes that compete to refresh the same credential. Never copy this configuration directory into the repository or into shared evidence. An ephemeral reference does not authenticate a new machine; that machine needs its own authorized login.

## Reproduce the host probes

Create a **different fresh workspace for every invocation**. For this configuration probe, run the following setup from the pinned sparkle checkout; it copies both bundles and warms a workspace-local dependency cache before entering the workspace. This resolves the cache permission and sandbox network blockers observed during validation. Use the same preparation for all cells.

```sh
eval_work=$(mktemp -d /private/tmp/sparkle-eval-work.XXXXXX)
mkdir -p "$eval_work/.agents/skills"
cp -R "$eval_repo/skills/define-workflow" "$eval_work/.agents/skills/"
cp -R "$eval_repo/skills/execute-workflow" "$eval_work/.agents/skills/"
printf '%s\n' 'matrix-preflight-20261008' > "$eval_work/fixture.txt"
UV_CACHE_DIR="$eval_work/.uv-cache" uv run \
  "$eval_work/.agents/skills/define-workflow/scripts/workflow.py" validate \
  "$eval_work/.agents/skills/define-workflow/assets/WORKFLOW.md"
cd "$eval_work"
```

The following commands run from that fresh workspace. Set `eval_prompt` to the probe text below. Redirect JSONL stdout and stderr to an evidence directory outside the workspace, and record the exact arguments and exit status. Fencing the command avoids interpreting prose punctuation as an argument.

````sh
eval_prompt=$(cat <<'PROMPT'
Configuration diagnostic only. Use your shell tool to run the exact command inside this fenced block in the current workspace:
```sh
cp fixture.txt answer.txt && cmp fixture.txt answer.txt && UV_CACHE_DIR=.uv-cache uv run --offline .agents/skills/define-workflow/scripts/workflow.py validate .agents/skills/define-workflow/assets/WORKFLOW.md && UV_CACHE_DIR=.uv-cache uv run --offline .agents/skills/execute-workflow/scripts/workflow.py validate .agents/skills/execute-workflow/assets/WORKFLOW.md
```
These are read-only structural helper checks, not workflow execution or publication. Dependencies have already been cached in .uv-cache. Report any error accurately. Reply with exactly MATRIX_PREFLIGHT_OK only if the command exits zero and both validation outputs say valid true. Do not access credentials or modify anything beyond answer.txt and runtime cache files.
PROMPT
)
````
```

Codex / Luna:

```sh
env -u OPENAI_API_KEY "$eval_codex" exec \
  --ignore-user-config --ignore-rules --skip-git-repo-check --ephemeral --json \
  -s workspace-write -c 'approval_policy="never"' \
  -c 'model_reasoning_effort="medium"' -m gpt-6-luna \
  "$eval_prompt" </dev/null
```

Codex / local:

```sh
env -u OPENAI_API_KEY "$eval_codex" exec \
  --ignore-user-config --ignore-rules --skip-git-repo-check --ephemeral --json \
  -s workspace-write -c 'approval_policy="never"' \
  -c 'model_reasoning_effort="medium"' -m gpt-oss:120b \
  -c 'model_provider="ollama-local"' -c 'model_context_window=131072' \
  -c 'model_providers.ollama-local={name="Local Ollama",base_url="http://127.0.0.1:11434/v1",wire_api="responses",requires_openai_auth=false,supports_websockets=false}' \
  "$eval_prompt" </dev/null
```

Pi / Luna:

```sh
env -u OPENAI_API_KEY PI_CODING_AGENT_DIR="$eval_pi_dir" "$eval_pi" \
  --offline --no-extensions --no-mcp --no-skills --no-context-files \
  --no-prompt-templates --no-themes --no-session --tools read,write,bash \
  --thinking medium --provider openai-codex --model gpt-6-luna \
  --mode json --print "$eval_prompt" </dev/null
```

Pi / local: use the same Pi command with `--provider ollama --model gpt-oss:120b`.

These host probes intentionally read known skill paths. Pi automatic skill discovery is disabled; the probe verifies access, not native discovery. Codex ignores user config/rules but still uses the host's authentication and may discover global skills. For actual usefulness runs, inventory and isolate those resources as required by the policy. Enable only the skill resources for the selected condition; exercise native skill discovery/invocation separately. Do not give the no-skill baseline these helper commands. All host probes used fresh sessions/workspaces; Pi's tools run with host-user permissions, so a temporary directory is not a security sandbox. The host recipes do not establish that all four cells work inside Docker.

The operator must check the actual transcript for successful tool calls and helper JSON validation results, require exit zero, independently compare `fixture.txt` and `answer.txt` byte for byte, and verify that the **final assistant message** is exactly the marker. Searching the entire transcript for a marker is invalid: prompts, command arguments, and error messages may contain it. A marker or process exit alone is insufficient. The diagnostic budget was 360 seconds per cell; retain timeouts and failed attempts.

## Existing Docker sandbox

Docker Sandboxes **v0.47.0** uses `sbx`; the old `docker sandbox` command has been removed. The earlier task created `codex-ollama-120b` with workspace `/private/tmp/codex-ollama-120b-workspace`. Availability and contents are local machine state, not repository artifacts. Attach with:

```sh
sbx run --name codex-ollama-120b
sbx exec codex-ollama-120b codex --version
```

Model selection was enabled with `sbx settings set feature.model true`; experimental features were already enabled. For a new temporary workspace, the native route is `sbx run --name NAME --model gpt-oss:120b --provider ollama codex /absolute/workspace`. Docker's [model configuration](https://docs.docker.com/ai/sandboxes/configuration/models/) explains the host Ollama route.

The template bundled Codex 0.149.1. Upgrade a new sandbox explicitly:

```sh
sbx exec -u root NAME npm install -g @openai/codex@0.162.0
```

Docker generated `[model_providers.ollama]`, which Codex 0.162.0 rejects because built-in provider names are reserved. Rename that custom provider and `model_provider` to `ollama-local`, and set its base URL to `http://host.docker.internal:11434/v1`. The existing sandbox was corrected this way. Its generated MCP configuration also needed `http_headers` instead of `headers` and removal of the unrecognized `type = "http"` field. Preserve other settings and credential handling; do not dump authentication files. Passing model-selection flags again can recreate the container, so recheck the CLI version and generated configuration afterward.

The earlier sandbox inference returned `OLLAMA_SANDBOX_OK`. Docker defaults Codex to bypassing approvals/internal sandboxing inside its external sandbox; host probes instead used Codex `workspace-write`. Do not combine those execution conditions within a paired comparison without recording the difference. Pi-in-Docker and subscription-in-Docker have not been validated by the host matrix.

## Observed validation, 2026-10-08

The tested skill resources came from commit `1eb5e9f4f58548c294782c0f5fbf1594891d00a7` (v0.1.2); this documentation contribution does not change those bundles. The first four-cell probe read `fixture.txt`, both `SKILL.md` files, and both helper directories; asked for an exact copy to `answer.txt`; and requested `MATRIX_PREFLIGHT_OK`. All cells reached their selected model and completed real read/write/shell tool calls. Codex used subscription login for Luna; Pi's transcripts identified `openai-codex`, `openai-codex-responses`, and `gpt-6-luna`. Local requests used the configured Ollama endpoints.

| Cell | First probe elapsed | Exact artifact | Final offline diagnostic |
| --- | --- | --- | --- |
| Codex / Luna | 10.02 s | Passed | Passed, 6.39 s |
| Pi / Luna | 9.48 s | Failed: missing trailing newline | Passed, 6.35 s |
| Codex / local | 230.74 s | Passed | Passed, 10.98 s |
| Pi / local | 22.18 s | Passed | Passed, 4.91 s |

All four final probes exited zero, produced byte-identical artifacts, returned exactly the final marker, and showed both bundled helpers returning `"valid": true` in successful tool results. These observations validate the four host configurations for inference, shell/file tools, and helper dependencies. They do not measure relative performance: the probes, cache warmth, and loaded-model state differ between rounds.

Pi / Luna's first run returned success despite omitting a byte. That is an observed instruction/verification failure, not a credential or tool-transport failure, and remains part of the evidence. The diagnostic with explicit `cp`/`cmp` and two helper invocations checks configuration/dependency readiness; it does not erase the first result or count as a usefulness improvement.

The second probe reached helpers successfully in both Pi cells; Codex was blocked by the default uv cache permissions and sandbox DNS restrictions. Both Codex cells reported those blockers accurately. A third probe with prewarmed workspace-local caches resolved those environment restrictions, but its command had an ambiguous trailing prose period that Codex / Luna treated as an extra CLI argument. The final, fourth probe uses the fenced command above in fresh workspaces and retains all earlier attempts. Infrastructure repairs and prompt corrections are configuration diagnostics, not scored baseline/candidate trials.

Codex / local emitted a model-catalog decode diagnostic while refreshing model metadata; actual inference and tool use succeeded. Keep stderr in evidence and recheck metadata when upgrading. These are configuration observations using synthetic fixtures, not completed authoring/execution evals or evidence that sparkle improves results.

Raw first-round transcripts and operator result records are local to `/private/tmp/sparkle-eval-preflight-20261008/`; diagnostics are under `round2/`, `round3/`, and `round4/`. Earlier operator marker flags were overly broad substring checks; the recorded operator assessments and final-round exact-message checks correct that limitation. Temporary evidence is not guaranteed to survive host cleanup. Preserve it privately if needed, with credentials excluded; only this sanitized summary and configuration templates are committed.
