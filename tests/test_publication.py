#!/usr/bin/env python3
"""Simulated GitHub receipts test recovery; no provider writes occur."""
import copy
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import publish as p


class Remote:
    def __init__(self):
        self.tag = None
        self.release = None
        self.data = {}
        self.writes = []
        self.lose_response = None

    def __call__(self, method, path, data=None, **kwargs):
        if method == 'GET' and '/git/ref/tags/' in path:
            return copy.deepcopy(self.tag)
        if method == 'GET' and '/assets/' in path:
            return self.data[int(path.rsplit('/', 1)[1])]
        self.writes.append((method, path))
        if path.endswith('/git/refs'):
            self.tag = {'object': {'type': 'commit', 'sha': data['sha']}}
            result = self.tag
        elif method == 'POST' and path.endswith('/releases'):
            self.release = dict(data, id=1, assets=[], html_url='https://example.test/release')
            result = self.release
        elif method == 'POST' and '/assets?name=' in path:
            asset = {'id': len(self.data) + 1, 'name': path.split('name=')[1]}
            self.data[asset['id']] = data
            self.release['assets'].append(asset)
            result = asset
        elif method == 'PATCH':
            self.release.update(data)
            result = self.release
        else:
            raise AssertionError((method, path))
        if self.lose_response and self.lose_response in path:
            self.lose_response = None
            raise RuntimeError('simulated lost response after write')
        return copy.deepcopy(result)


class Publication(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output = Path(self.temp.name)
        (self.output/'RELEASE_NOTES.md').write_text('fixture notes')
        (self.output/'skill.zip').write_bytes(b'fixture archive')
        self.selected = {'head': 'a'*40, 'tag': 'v0.1.0', 'version': '0.1.0'}
        self.remote = Remote()

    def publish(self, verify=lambda: None):
        return p.publish_bundle(self.selected, self.output, copy.deepcopy(self.remote.release), self.remote, verify,
                                lambda tag, path, rid: self.remote('POST', f'/releases/{rid}/assets?name={path.name}', path.read_bytes()))

    def test_upload_uses_sized_file_without_clobber(self):
        path = self.output/'skill.zip'
        receipt = {'id': 42, 'name': path.name}
        with mock.patch.object(p.subprocess, 'run') as command, mock.patch.object(p, 'api', return_value={'assets': [receipt]}):
            self.assertEqual(p.upload('v0.1.0', path, 1), receipt)
        args = command.call_args.args[0]
        self.assertEqual(args, ['gh', 'release', 'upload', 'v0.1.0', str(path), '--repo', p.REPO])
        self.assertNotIn('input', command.call_args.kwargs)
        self.assertNotIn('--clobber', args)

    def test_publish_then_read_only_retry(self):
        self.assertTrue(self.publish()['published'])
        self.assertFalse(self.remote.release['draft'])
        self.assertTrue(self.remote.release['prerelease'])
        writes = len(self.remote.writes)
        self.publish()
        self.assertEqual(len(self.remote.writes), writes)

    def test_lost_responses_are_reconciled(self):
        for point in ('/git/refs', '/releases', '/assets?name=', '/releases/1'):
            with self.subTest(point=point):
                self.remote = Remote()
                self.remote.lose_response = point
                with self.assertRaisesRegex(RuntimeError, 'lost response'):
                    self.publish()
                self.publish()
                self.assertEqual(len(self.remote.release['assets']), 2)
                self.assertFalse(self.remote.release['draft'])

    def test_tag_metadata_and_asset_collisions_fail(self):
        self.remote.tag = {'object': {'type': 'commit', 'sha': 'b'*40}}
        with self.assertRaisesRegex(ValueError, 'existing tag'):
            self.publish()
        self.remote = Remote()
        self.publish()
        (self.output/'skill.zip').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'differs'):
            self.publish()
        (self.output/'RELEASE_NOTES.md').write_text('changed metadata')
        with self.assertRaisesRegex(ValueError, 'metadata differs'):
            self.publish()

    def test_failed_tagged_install_leaves_draft(self):
        def failure():
            raise RuntimeError('tagged install unavailable')
        with self.assertRaisesRegex(RuntimeError, 'unavailable'):
            self.publish(failure)
        self.assertTrue(self.remote.release['draft'])
        self.assertEqual(self.remote.release['assets'], [])
        self.publish()
        self.assertFalse(self.remote.release['draft'])

    def test_missing_published_asset_is_not_replaced(self):
        self.publish()
        self.remote.release['assets'].pop()
        with self.assertRaisesRegex(ValueError, 'missing assets'):
            self.publish()


class Preflight(unittest.TestCase):
    def setUp(self):
        from test_releases import Releases
        self.fixture = Releases()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.root = self.fixture.root
        self.selected = self.fixture.plan()
        self.main = self.selected['head']
        self.verified = True
        self.tags = []
        self.releases = []

    def request(self, method, path, **kwargs):
        self.assertEqual(method, 'GET')
        if '/heads/main' in path:
            return {'object': {'sha': self.main}}
        if '/commits/' in path:
            return {'commit': {'verification': {'verified': self.verified}}}
        if '/matching-refs/' in path:
            return self.tags
        return self.releases

    def check(self, resume=False):
        return p.preflight(self.selected, resume, self.root, self.request)

    def test_current_signed_main_and_unsigned_rejection(self):
        self.assertIsNone(self.check())
        self.verified = False
        with self.assertRaisesRegex(ValueError, 'verified signature'):
            self.check()

    def test_stale_checkout_requires_existing_receipt_to_resume(self):
        self.main = self.fixture.commit('docs: new main')
        with self.assertRaisesRegex(ValueError, 'stale main'):
            self.check()
        with self.assertRaisesRegex(ValueError, 'existing release'):
            self.check(resume=True)
        self.tags = [{'ref': 'refs/tags/v0.1.0', 'object': {'type': 'commit', 'sha': self.selected['head']}}]
        self.check(resume=True)

    def test_remote_tag_races_and_unfinished_previous_release(self):
        self.tags = [{'ref': 'refs/tags/v0.2.0', 'object': {'type': 'commit', 'sha': self.main}}]
        with self.assertRaisesRegex(ValueError, 'remote tags changed'):
            self.check()
        self.fixture.git('tag', 'v0.1.0')
        old = self.main
        self.main = self.fixture.commit('fix: next')
        self.selected = self.fixture.plan()
        self.tags = [{'ref': 'refs/tags/v0.1.0', 'object': {'type': 'commit', 'sha': old}}]
        with self.assertRaisesRegex(ValueError, 'finish interrupted'):
            self.check()
        self.releases = [{'tag_name': 'v0.1.0', 'draft': False}]
        self.check()


if __name__ == '__main__':
    unittest.main()
