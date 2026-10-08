#!/usr/bin/env python3
"""Locally reproducible project release planning; no external writes by default."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.compile(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z')
HEADER = re.compile(r'(feat|fix|perf|docs|refactor|style|test|build|ci|chore|revert)(?:\([^()\r\n]+\))?(!)?: ([^\r\n]+)\Z')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def git(*args, root=ROOT):
    return subprocess.check_output(['git', *args], cwd=root, text=True).strip()


def oid(ref, root=ROOT):
    return git('rev-parse', '--verify', '--end-of-options', ref + '^{commit}', root=root)


def ancestor(base, head, root=ROOT):
    return subprocess.run(['git', 'merge-base', '--is-ancestor', base, head], cwd=root).returncode == 0


def version(value):
    match = VERSION.fullmatch(value)
    need(match, f'invalid release version: {value}; use MAJOR.MINOR.PATCH without leading zeroes')
    return tuple(map(int, match.groups()))


def config(ref, root=ROOT):
    value = json.loads(git('show', f'{ref}:release.json', root=root))
    need(isinstance(value, dict) and set(value) == {'schema', 'initial_version', 'stable'}, 'invalid release.json fields')
    need(type(value['schema']) is int and value['schema'] == 1, 'unsupported release schema')
    need(value['initial_version'] == '0.1.0', 'initial release must be 0.1.0')
    need(type(value['stable']) is bool, 'stable must be boolean')
    return value


def parse_commit(message):
    lines = message.strip().splitlines()
    match = HEADER.fullmatch(lines[0] if lines else '')
    need(match and match[3].strip(), f'not a Conventional Commit: {lines[0] if lines else "<empty>"}')
    need(len(lines) < 2 or lines[1] == '', 'commit body must follow a blank line')
    markers = [line for line in lines[2:] if line.startswith(('BREAKING CHANGE:', 'BREAKING-CHANGE:'))]
    need(all(line.split(':', 1)[1].strip() for line in markers), 'breaking-change footer requires an explanation')
    return {'type': match[1], 'breaking': bool(match[2] or markers), 'subject': lines[0]}


def commits(base, head, root=ROOT):
    head = oid(head, root)
    if base:
        base = oid(base, root)
        need(ancestor(base, head, root), 'base is not an ancestor of head; integrate current main first')
    revisions = git('rev-list', '--reverse', '--topo-order', '--no-merges', f'{base}..{head}' if base else head, root=root)
    result = []
    for sha in revisions.splitlines():
        try:
            parsed = parse_commit(git('show', '-s', '--format=%B', sha, root=root))
        except ValueError as error:
            raise ValueError(f'{sha[:12]}: {error}') from error
        result.append(dict(sha=sha, **parsed))
    return result


def next_version(previous, changes, stable):
    if previous is None:
        need(not stable, 'publish 0.1.0 before promoting to stable')
        return '0.1.0'
    major, minor, patch = version(previous)
    need(major == 0 or stable, 'cannot return to unstable policy after 1.0')
    if major == 0 and stable:
        return '1.0.0'
    breaking = any(c['breaking'] for c in changes)
    if breaking and major:
        return f'{major + 1}.0.0'
    if breaking or any(c['type'] == 'feat' for c in changes):
        return f'{major}.{minor + 1}.0'
    if any(c['type'] in {'fix', 'perf'} for c in changes):
        return f'{major}.{minor}.{patch + 1}'
    return None


def history(head, root=ROOT):
    need(git('rev-parse', '--is-shallow-repository', root=root) == 'false', 'fetch full history and tags before planning')
    tags = git('tag', '--list', 'v*', root=root).splitlines()
    releases = sorted(((version(tag[1:]), tag, oid(tag, root)) for tag in tags))
    previous = None
    for _, tag, sha in releases:
        need(ancestor(sha, head, root), f'{tag} is outside this history; fetch and integrate current main')
        base = previous['sha'] if previous else None
        need(base != sha, 'multiple release versions on the same commit')
        changes = commits(base, sha, root)
        settings = config(sha, root)
        expected = next_version(previous['version'] if previous else None, changes, settings['stable'])
        need(tag == f'v{expected}', f'{tag} violates semantic release policy; expected v{expected}')
        previous = {'tag': tag, 'version': tag[1:], 'sha': sha, 'changes': changes}
        yield previous


def plan(head='HEAD', root=ROOT):
    head = oid(head, root)
    settings = config(head, root)
    releases = list(history(head, root))
    replay = bool(releases and releases[-1]['sha'] == head)
    prior = releases[:-1] if replay else releases
    previous = prior[-1] if prior else None
    changes = commits(previous['sha'] if previous else None, head, root)
    selected = next_version(previous['version'] if previous else None, changes, settings['stable'])
    return {'head': head, 'previous': previous['tag'] if previous else None,
            'version': selected, 'tag': f'v{selected}' if selected else None,
            'stable': settings['stable'], 'replay': replay, 'commits': changes}


def files_at(prefix, head, root=ROOT):
    paths = git('ls-tree', '-r', '--name-only', head, '--', prefix, root=root).splitlines()
    result = {}
    for path in paths:
        mode = git('ls-tree', head, '--', path, root=root).split()[0]
        need(mode in {'100644', '100755'}, f'unsupported release file mode: {path}')
        result[path] = subprocess.check_output(['git', 'show', f'{head}:{path}'], cwd=root)
    return result


def check_bundles(head, root=ROOT):
    for name in ('define-workflow', 'execute-workflow'):
        skill = files_at(f'skills/{name}/', head, root)
        need(f'skills/{name}/SKILL.md' in skill, f'missing skill entry: {name}')
        for area in ('scripts', 'references', 'assets'):
            source_prefix = f'shared/{area}/'
            target_prefix = f'skills/{name}/{area}/'
            source = {p[len(source_prefix):]: data for p, data in files_at(source_prefix, head, root).items()}
            target = {p[len(target_prefix):]: data for p, data in skill.items() if p.startswith(target_prefix)}
            need(source and source == target, f'stale or incomplete bundle: {name}/{area}')


def notes(tag, head, changes):
    lines = [f'## {tag}', '', f'Source: `{head}`', '']
    if version(tag[1:])[0] == 0:
        lines += ['Initial development: backwards compatibility and regression testing are not required.', '']
    for title, selected in (
        ('Breaking changes', [c for c in changes if c['breaking']]),
        ('Features', [c for c in changes if not c['breaking'] and c['type'] == 'feat']),
        ('Fixes and performance', [c for c in changes if not c['breaking'] and c['type'] in {'fix', 'perf'}]),
        ('Other changes', [c for c in changes if not c['breaking'] and c['type'] not in {'feat', 'fix', 'perf'}]),
    ):
        if selected:
            lines += [f'### {title}', '']
            for c in selected:
                subject = re.sub(r'([\\`*_{}\[\]()<>!#|])', r'\\\1', c['subject'])
                lines.append(f"- {subject} ([{c['sha'][:12]}](https://github.com/tclasen/sparkle/commit/{c['sha']}))")
            lines.append('')
    return '\n'.join(lines)


def build(output, root=ROOT):
    need(not git('status', '--porcelain', '--untracked-files=no', root=root), 'commit tracked changes before building a release')
    selected = plan(root=root)
    need(selected['version'], 'no releasable changes')
    head, tag = selected['head'], selected['tag']
    check_bundles(head, root)
    output = Path(output).resolve()
    need(not output.exists(), 'output directory already exists; choose a fresh directory')
    output.mkdir(parents=True)
    metadata = {'version': selected['version'], 'tag': tag, 'commit': head}
    for name in ('define-workflow', 'execute-workflow'):
        source = files_at(f'skills/{name}/', head, root)
        with zipfile.ZipFile(output/f'{name}-{tag}.zip', 'w', compression=zipfile.ZIP_STORED) as archive:
            members = {path.removeprefix('skills/'): data for path, data in source.items()}
            entry = f'{name}/SKILL.md'
            text = members[entry].decode()
            text, count = re.subn(r'(?m)^  version: "unreleased"$', f'  version: "{selected["version"]}"', text)
            need(count == 1, f'{name}: expected one unreleased skill version marker')
            members[entry] = text.encode()
            members[f'{name}/RELEASE.json'] = (json.dumps(metadata, indent=2, sort_keys=True) + '\n').encode()
            for path, data in sorted(members.items()):
                info = zipfile.ZipInfo(path, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
    current = notes(tag, head, selected['commits'])
    previous = [item for item in history(head, root) if item['tag'] != tag]
    changelog = '# Changelog\n\n' + current + ''.join('\n' + notes(item['tag'], item['sha'], item['changes']) for item in reversed(previous))
    (output/'RELEASE_NOTES.md').write_text(current)
    (output/'CHANGELOG.md').write_text(changelog)
    (output/'release.json').write_text(json.dumps(metadata, indent=2, sort_keys=True) + '\n')
    checksums = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(output.iterdir())}
    (output/'SHA256SUMS.json').write_text(json.dumps(checksums, indent=2, sort_keys=True) + '\n')
    return selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('lint'); p.add_argument('--base'); p.add_argument('--head', default='HEAD')
    p = sub.add_parser('plan'); p.add_argument('--head', default='HEAD')
    p = sub.add_parser('build'); p.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.command == 'lint':
        result = {'valid': True, 'commits': len(commits(args.base, args.head))}
    elif args.command == 'build':
        result = build(args.output)
    else:
        result = plan(args.head)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
