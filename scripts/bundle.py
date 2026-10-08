#!/usr/bin/env python3
"""Build complete skill bundles from shared sources, or check freshness."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--check', action='store_true')
args = p.parse_args()
stale = []
for name in ('define-workflow', 'execute-workflow'):
    for area in ('scripts', 'references', 'assets'):
        source = ROOT/'shared'/area
        target = ROOT/'skills'/name/area
        expected = {f.relative_to(source): f.read_bytes() for f in source.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
        actual = {f.relative_to(target): f.read_bytes() for f in target.rglob('*') if f.is_file() and '__pycache__' not in f.parts}
        if expected != actual: stale.append(f'{name}/{area}')
        if not args.check:
            if target.exists(): shutil.rmtree(target)
            shutil.copytree(source, target, ignore=shutil.ignore_patterns('__pycache__'))
if args.check and stale:
    p.exit(1, 'Stale bundles: '+', '.join(stale)+'\nRun python3 scripts/bundle.py\n')
print('Bundles current.' if args.check else 'Bundles generated.')
