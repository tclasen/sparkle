#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Actual repository-local skills CLI installation plus standalone-resource smoke tests."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CLI = ['npx', '--yes', 'skills@1.7.1']


def run(command, cwd, env):
    print('$ ' + shlex.join(map(str, command)), flush=True)
    result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, text=True, capture_output=True, timeout=120)
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    print(result.stdout.strip(), flush=True)
    return result.stdout


def files(folder):
    return {str(p.relative_to(folder)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', default=str(ROOT), help='skills CLI source: local checkout or version-pinned GitHub tree URL')
    parser.add_argument('--expected-root', type=Path, default=ROOT, help='checkout whose skill contents must match the installed source')
    parser.add_argument('--smoke-only', action='store_true', help='validate current installation without the behavioral regression walkthrough')
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix='workflow-install-') as temp:
        base = Path(temp)
        target = base / 'project'; target.mkdir()
        env = os.environ.copy()
        env['DISABLE_TELEMETRY'] = '1'
        env.setdefault('npm_config_cache', str(base / 'npm-cache'))
        env.setdefault('UV_CACHE_DIR', str(base / 'uv-cache'))
        run(CLI + ['--version'], target, env)
        run(CLI + ['add', args.source, '--skill', 'define-workflow', 'execute-workflow', '-a', 'codex', '-y', '--copy', '--json'], target, env)
        for name in ('define-workflow', 'execute-workflow'):
            # CLI versions may use the common .agents location or a Codex-local copy.
            candidates = [target / '.agents/skills' / name, target / '.codex/skills' / name]
            installed = next((p for p in candidates if (p / 'SKILL.md').is_file()), None)
            assert installed is not None, f'{name} was not installed locally'
            assert files(installed) == files(args.expected_root / 'skills' / name), f'lost/changed installed resources: {name}'
            isolated = base / ('isolated-' + name); isolated.mkdir()
            skill = isolated / name
            shutil.copytree(installed, skill)
            for doc in skill.rglob('*.md'):
                for link in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
                    if not re.match(r'https?://', link):
                        assert (doc.parent / link).is_file(), f'broken relative resource: {doc}: {link}'
            script = skill / 'scripts/workflow.py'
            # The executable shebang and inline metadata are exercised through uv, not Python imports.
            run(['uv', 'run', script, 'validate', skill / 'assets/WORKFLOW.md'], isolated, env)
            if args.smoke_only:
                continue
            run(['uv', 'run', script, 'publish', skill / 'assets/WORKFLOW.md', '--root', isolated, '--version', '1.0.0'], isolated, env)
            run(['uv', 'run', script, 'verify-release', 'example-workflow', '1.0.0', '--root', isolated], isolated, env)
            run(['uv', 'run', script, 'project', 'sample', '--root', isolated, '--brief', 'Isolated installation smoke test'], isolated, env)
            inputs = isolated / 'inputs.json'; inputs.write_text('{"topic":"Isolated input"}')
            environment = isolated / 'environment.json'; environment.write_text('{"executor":"install-test","capabilities":[],"skills":{}}')
            output = run(['uv', 'run', script, 'start', 'sample', 'example-workflow', '--root', isolated, '--inputs', inputs, '--environment', environment, '--owner', 'isolated-coordinator'], isolated, env)
            import json
            run_path = json.loads(output)['run']
            run_dir = Path(run_path)
            (run_dir / 'artifacts/proof.txt').write_text('Isolated fixture evidence')
            result_file = isolated / 'result.json'
            result_file.write_text(json.dumps({'assessment': 'Fixture criteria passed', 'evidence': ['artifacts/proof.txt']}))
            revision = 0
            for step in ('prepare', 'check'):
                run(['uv', 'run', script, 'context', run_path, '/steps/' + step], isolated, env)
                for operation in ('begin', 'complete'):
                    extra = ['--result', result_file] if operation == 'complete' else []
                    output = run(['uv', 'run', script, 'step', run_path, '/steps/' + step, operation, '--owner', 'isolated-coordinator', '--revision', revision, *extra], isolated, env)
                    revision = json.loads(output)['revision']
            result_file.write_text(json.dumps({'passed': True, 'assessment': 'Fixture final criteria passed', 'evidence': ['artifacts/proof.txt']}))
            run(['uv', 'run', script, 'finish', run_path, '--result', result_file, '--owner', 'isolated-coordinator', '--revision', revision], isolated, env)
            run(['uv', 'run', script, 'validate-run', run_path], isolated, env)
            run(['uv', 'run', script, 'release', run_path, '--owner', 'isolated-coordinator'], isolated, env)
            # Exercise the optional coordination interface with only this installed skill.
            output = run(['uv', 'run', script, 'start', 'sample', 'example-workflow', '--root', isolated,
                          '--inputs', inputs, '--environment', environment, '--owner', 'isolated-coordinator',
                          '--coordination', skill / 'assets/coordination.json'], isolated, env)
            peer_run = Path(json.loads(output)['run'])
            (peer_run / 'artifacts/observation.txt').write_text('Simulated isolated ticket observation')
            event = isolated / 'event.json'
            event.write_text(json.dumps(dict(id='observation', kind='claim_observation',
                claim_id='replace-with-unique-claim-id', observed_at='2026-10-08T12:00:00Z',
                explanation='Simulated read', evidence=['artifacts/observation.txt'], accessible=True,
                claim_seen=True, active_claims=['replace-with-unique-claim-id'])))
            run(['uv', 'run', script, 'coordination', peer_run, 'record', '--result', event,
                 '--owner', 'isolated-coordinator', '--revision', '0'], isolated, env)
            observed = json.loads(run(['uv', 'run', script, 'coordination', peer_run, 'show'], isolated, env))
            assert len(observed['coordination']['events']) == 1
            ready = json.loads(run(['uv', 'run', script, 'ready', peer_run], isolated, env))
            assert ready['coordination']['blockers'] == ['dependency-unassessed']
            run(['uv', 'run', script, 'validate-run', peer_run], isolated, env)
        print('PASS: both actual CLI installations retained all resources and operated independently.')


if __name__ == '__main__':
    main()
