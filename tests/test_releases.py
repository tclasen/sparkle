#!/usr/bin/env python3
"""Release policy checks using temporary Git histories and no provider writes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('release', Path(__file__).resolve().parents[1]/'scripts/release.py')
r = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(r)


class Releases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.git('init', '-b', 'main')
        self.git('config', 'user.name', 'Fixture')
        self.git('config', 'user.email', 'fixture@example.test')
        self.git('config', 'commit.gpgsign', 'false')
        self.settings = {'schema': 1, 'initial_version': '0.1.0', 'stable': False}
        self.save_config()
        self.commit('chore: initialize')

    def git(self, *args):
        return r.git(*args, root=self.root)

    def save_config(self):
        (self.root/'release.json').write_text(json.dumps(self.settings))

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '--allow-empty', '-m', message)
        return self.git('rev-parse', 'HEAD')

    def plan(self):
        return r.plan(root=self.root)

    def test_initial_and_bumps(self):
        self.assertEqual(self.plan()['version'], '0.1.0')
        self.git('tag', 'v0.1.0')
        self.assertTrue(self.plan()['replay'])
        self.commit('docs: clarify')
        self.assertIsNone(self.plan()['version'])
        self.commit('fix(api): repair')
        self.assertEqual(self.plan()['version'], '0.1.1')
        self.commit('feat: add option')
        self.assertEqual(self.plan()['version'], '0.2.0')
        self.commit('refactor!: replace format')
        self.assertEqual(self.plan()['version'], '0.2.0')
        self.git('tag', 'v0.2.0')
        self.commit('perf: optimize')
        self.assertEqual(self.plan()['version'], '0.2.1')

    def test_stable_is_explicit_and_irreversible(self):
        self.git('tag', 'v0.1.0')
        self.commit('fix: change\n\nBREAKING CHANGE: incompatible')
        self.assertEqual(self.plan()['version'], '0.2.0')
        self.settings['stable'] = True
        self.save_config()
        self.commit('chore: graduate')
        self.assertEqual(self.plan()['version'], '1.0.0')
        self.git('tag', 'v1.0.0')
        self.commit('feat: add')
        self.assertEqual(self.plan()['version'], '1.1.0')
        self.commit('fix: change\n\nBREAKING-CHANGE: incompatible')
        self.assertEqual(self.plan()['version'], '2.0.0')
        self.settings['stable'] = False
        self.save_config()
        self.commit('chore: revert policy')
        with self.assertRaisesRegex(ValueError, 'unstable'):
            self.plan()

    def test_lint_merge_and_invalid_commit(self):
        self.git('checkout', '-b', 'topic')
        self.commit('feat(core): valid')
        self.git('checkout', 'main')
        self.git('merge', '--no-ff', 'topic', '-m', 'GitHub merge title (#1)')
        self.assertEqual(len(r.commits(None, 'HEAD', self.root)), 2)
        self.commit('random message')
        with self.assertRaisesRegex(ValueError, 'Conventional'):
            self.plan()
        for message in ('fix: ', 'feat: title\nbody', 'fix: title\n\nBREAKING CHANGE:'):
            with self.subTest(message=message), self.assertRaises(ValueError):
                r.parse_commit(message)

    def test_invalid_tags_and_initial_config(self):
        for tag in ('v00.1.0', 'v0.1.0-rc.1', 'v0.2.0'):
            self.git('tag', tag)
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                self.plan()
            self.git('tag', '-d', tag)
        self.settings['stable'] = True
        self.save_config()
        self.commit('chore: premature graduation')
        with self.assertRaisesRegex(ValueError, '0.1.0'):
            self.plan()

    def test_wrong_bump_and_divergent_tag(self):
        self.git('tag', 'v0.1.0')
        self.git('checkout', '-b', 'other')
        self.commit('feat: divergent')
        self.git('tag', 'v0.2.0')
        self.git('checkout', 'main')
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.plan()
        self.git('tag', '-d', 'v0.2.0')
        self.commit('fix: patch')
        self.git('tag', 'v0.3.0')
        with self.assertRaisesRegex(ValueError, 'expected v0.1.1'):
            self.plan()


if __name__ == '__main__':
    unittest.main()
