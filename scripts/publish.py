#!/usr/bin/env python3
"""Preview by default; publish immutable tags/assets only with --execute."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

import release

REPO = 'tclasen/sparkle'
PREFIX = f'repos/{REPO}'


def api(method, path, data=None, *, missing=False, binary=False):
    command = ['gh', 'api', '--method', method, path]
    payload = None
    if binary:
        command += ['--header', 'Accept: application/octet-stream']
    if data is not None:
        payload = data if isinstance(data, bytes) else json.dumps(data).encode()
        command += ['--input', '-', '--header', 'Content-Type: ' + ('application/octet-stream' if isinstance(data, bytes) else 'application/json')]
    result = subprocess.run(command, input=payload, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        error = result.stderr.decode(errors='replace')
        if missing and 'HTTP 404' in error:
            return None
        raise RuntimeError(f'GitHub {method} failed: {error.strip()}')
    if binary:
        return result.stdout
    return json.loads(result.stdout) if result.stdout else None


def releases(request=api):
    page = 1
    result = []
    while True:
        batch = request('GET', f'{PREFIX}/releases?per_page=100&page={page}')
        result.extend(batch)
        if len(batch) < 100:
            return result
        page += 1


def preflight(selected, resume=False, root=release.ROOT, request=api):
    main = request('GET', f'{PREFIX}/git/ref/heads/main')['object']['sha']
    head = selected['head']
    release.need(release.ancestor(head, main, root), 'release source must be on main; fetch upstream main first')
    release.need(main == head or resume, 'stale main checkout; use current main or --resume for an existing interrupted publication')
    release.need(request('GET', f'{PREFIX}/commits/{head}')['commit']['verification']['verified'], 'release source commit must have a verified signature')
    known = {item['tag_name']: item for item in releases(request)}
    remote = {item['ref'].removeprefix('refs/tags/'): item['object'] for item in request('GET', f'{PREFIX}/git/matching-refs/tags/v')}
    local = {tag: release.oid(tag, root) for tag in release.git('tag', '--list', 'v*', root=root).splitlines()}
    release.need(set(remote) - set(local) <= {selected['tag']}, 'remote tags changed; fetch all tags before publishing')
    for tag, sha in local.items():
        release.need(tag in remote and remote[tag]['type'] == 'commit' and remote[tag]['sha'] == sha, f'local/remote tag mismatch: {tag}')
    if selected['tag'] in remote:
        obj = remote[selected['tag']]
        release.need(obj['type'] == 'commit' and obj['sha'] == head, 'release tag already targets different content')
    if resume and main != head:
        release.need(selected['tag'] in remote or selected['tag'] in known, 'resume requires an existing release or tag')
    for tag, item in known.items():
        release.need(not (tag.startswith('v') and item['draft'] and tag != selected['tag']), f'finish interrupted draft {tag} from its original checkout with --resume first')
    if selected['previous']:
        prior = known.get(selected['previous'])
        release.need(prior and not prior['draft'], f'finish interrupted release {selected["previous"]} from its tagged checkout with --resume first')
    return known.get(selected['tag'])


def upload(tag, path, release_id):
    # The file-oriented CLI sets Content-Length; streamed gh api stdin does not.
    # Never use --clobber: existing content must be inspected, not replaced.
    subprocess.run(['gh', 'release', 'upload', tag, str(path), '--repo', REPO], check=True)
    record = api('GET', f'{PREFIX}/releases/{release_id}')
    matches = [asset for asset in record['assets'] if asset['name'] == path.name]
    release.need(len(matches) == 1, f'upload receipt missing or ambiguous: {path.name}')
    return matches[0]


def publish_bundle(selected, output, existing=None, request=api, verify_install=lambda: None, uploader=upload):
    """Inspect every existing receipt before writing; never overwrite published content."""
    head, tag = selected['head'], selected['tag']
    output = Path(output)
    body = (output/'RELEASE_NOTES.md').read_text()
    expected = {'tag_name': tag, 'target_commitish': head, 'name': tag, 'body': body,
                'prerelease': release.version(selected['version'])[0] == 0}
    tag_ref = request('GET', f'{PREFIX}/git/ref/tags/{tag}', missing=True)
    if tag_ref:
        release.need(tag_ref['object'] == {'type': 'commit', 'sha': head} or
                     (tag_ref['object'].get('type') == 'commit' and tag_ref['object'].get('sha') == head),
                     'existing tag does not match release source')
    else:
        request('POST', f'{PREFIX}/git/refs', {'ref': f'refs/tags/{tag}', 'sha': head})
    if existing:
        release.need(all(existing.get(key) == value for key, value in expected.items()), 'existing release metadata differs; inspect before retrying')
        record = existing
    else:
        record = request('POST', f'{PREFIX}/releases', dict(expected, draft=True))
    # The actual documented source URL is checked before making the release public.
    verify_install()
    assets = record['assets']
    names = [asset['name'] for asset in assets]
    release.need(len(names) == len(set(names)), 'duplicate release asset names')
    expected_names = {p.name for p in output.iterdir()}
    release.need(set(names) <= expected_names, 'unexpected release assets; inspect before retrying')
    for path in sorted(output.iterdir()):
        found = next((item for item in assets if item['name'] == path.name), None)
        if found:
            actual = request('GET', f'{PREFIX}/releases/assets/{found["id"]}', binary=True)
            release.need(actual == path.read_bytes(), f'existing asset differs: {path.name}; refusing overwrite')
        else:
            release.need(record['draft'], 'published release has missing assets; refusing mutation')
            receipt = uploader(tag, path, record['id'])
            actual = request('GET', f'{PREFIX}/releases/assets/{receipt["id"]}', binary=True)
            release.need(actual == path.read_bytes(), f'uploaded asset failed verification: {path.name}')
    if record['draft']:
        record = request('PATCH', f'{PREFIX}/releases/{record["id"]}', {'draft': False, 'make_latest': 'false' if expected['prerelease'] else 'true'})
    return {'tag': tag, 'url': record['html_url'], 'published': True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='fresh local output directory')
    parser.add_argument('--execute', action='store_true', help='authorize remote tag/release writes')
    parser.add_argument('--resume', action='store_true', help='resume an existing interrupted release from its original commit')
    args = parser.parse_args()
    selected = release.plan()
    existing = preflight(selected, args.resume) if args.execute else None
    if not selected['version']:
        print(json.dumps({'published': False, 'reason': 'no releasable changes'}))
        return
    release.build(args.output)
    if not args.execute:
        print(json.dumps(dict(selected, published=False, output=args.output), indent=2))
        return
    def verify_install():
        subprocess.run(['uv', 'run', release.ROOT/'tests/verify_install.py', '--source',
                        f'https://github.com/{REPO}/tree/{selected["tag"]}', '--smoke-only'], check=True)
    print(json.dumps(publish_bundle(selected, args.output, existing, verify_install=verify_install), indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
