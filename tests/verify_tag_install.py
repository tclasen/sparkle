#!/usr/bin/env python3
"""Exercise the documented skills.sh GitHub tag URL against a local Git fixture.

Git's URL rewrite keeps the repository download local; npm/uv may need network.
This verifies CLI ref parsing and installed bytes, not GitHub provider availability.
"""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='sparkle-tag-install-') as temp:
    repo = Path(temp)/'fixture.git'
    repo.mkdir()
    shutil.copytree(ROOT/'skills', repo/'skills', ignore=shutil.ignore_patterns('__pycache__'))
    for args in (['init', '-b', 'main'], ['config', 'user.name', 'Fixture'],
                 ['config', 'user.email', 'fixture@example.test'], ['config', 'commit.gpgsign', 'false'],
                 ['add', '.'], ['commit', '-m', 'feat: fixture'], ['tag', 'v0.1.0']):
        subprocess.run(['git', *args], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    # Change main after tagging: matching the tag must not accidentally install main.
    (repo/'skills/define-workflow/SKILL.md').write_text('invalid main sentinel')
    subprocess.run(['git', 'commit', '-am', 'test: distinguish main from tag'], cwd=repo, check=True, stdout=subprocess.DEVNULL)
    env = os.environ.copy()
    count = int(env.get('GIT_CONFIG_COUNT', '0'))
    for offset, suffix in enumerate(('.git', '')):
        env[f'GIT_CONFIG_KEY_{count + offset}'] = f'url.{repo.as_uri()}.insteadOf'
        env[f'GIT_CONFIG_VALUE_{count + offset}'] = 'https://github.com/tclasen/sparkle' + suffix
    env['GIT_CONFIG_COUNT'] = str(count + 2)
    subprocess.run(['uv', 'run', ROOT/'tests/verify_install.py', '--source',
                    'https://github.com/tclasen/sparkle/tree/v0.1.0', '--smoke-only'],
                   env=env, check=True)
    print('PASS: skills CLI selected the tagged fixture instead of main; both skills match.')
