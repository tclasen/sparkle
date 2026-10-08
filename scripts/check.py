#!/usr/bin/env python3
"""The same read-only validation entry point runs locally and in GitHub Actions."""
import argparse
import ast
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import release

ROOT = release.ROOT


def run(*args):
    print('+ ' + ' '.join(map(str, args)), flush=True)
    subprocess.run(list(map(str, args)), cwd=ROOT, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', help='lint commits and whitespace since this ancestor; omit to check all commits')
    args = parser.parse_args()
    selected = release.plan()
    release.commits(args.base, 'HEAD')
    run('git', 'diff', '--check', *([args.base, 'HEAD'] if args.base else []))
    for name in release.git('ls-files', '--cached', '--others', '--exclude-standard').splitlines():
        path = ROOT/name
        if path.suffix == '.py':
            ast.parse(path.read_text(), filename=name)
        elif path.suffix == '.json':
            json.loads(path.read_text())
        elif path.suffix == '.md':
            for link in re.findall(r'\]\(([^)]+)\)', path.read_text()):
                if not link.startswith(('https://', 'http://', '#')):
                    release.need((path.parent/link.split('#')[0]).is_file(), f'broken relative link in {name}: {link}')
    run('go', 'run', 'github.com/rhysd/actionlint/cmd/actionlint@v1.7.12', '-shellcheck=', '-pyflakes=')
    run(sys.executable, 'scripts/bundle.py', '--check')
    run(sys.executable, 'tests/test_releases.py')
    run(sys.executable, 'tests/test_publication.py')
    run('uv', 'run', 'tests/verify_install.py', *([] if selected['stable'] else ['--smoke-only']))
    run(sys.executable, 'tests/verify_tag_install.py')
    if selected['stable']:
        run('uv', 'run', 'tests/test_workflows.py')
    else:
        print('Pre-1.0: no backwards-compatibility or behavioral regression gate.', flush=True)
    if selected['version']:
        with tempfile.TemporaryDirectory(prefix='sparkle-release-check-') as temp:
            output = Path(temp)/'release'
            release.build(output)
            checksums = json.loads((output/'SHA256SUMS.json').read_text())
            release.need(all(release.hashlib.sha256((output/name).read_bytes()).hexdigest() == digest
                             for name, digest in checksums.items()), 'release checksums do not match')
    print(json.dumps({'valid': True, 'next_version': selected['version'], 'stable_policy': selected['stable']}))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
