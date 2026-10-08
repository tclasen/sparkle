#!/usr/bin/env python3
"""Release policy checks using temporary Git histories and no provider writes."""
import importlib.util
import json
import shutil
import zipfile
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

    def package_fixture(self):
        source = Path(__file__).resolve().parents[1]
        for folder in ('skills', 'shared'):
            shutil.copytree(source/folder, self.root/folder, ignore=shutil.ignore_patterns('__pycache__'))
        self.commit('feat: package skills')

    def test_reproducible_packages_and_metadata(self):
        self.package_fixture()
        with tempfile.TemporaryDirectory() as temp:
            first, second = Path(temp)/'first', Path(temp)/'second'
            selected = r.build(first, self.root)
            r.build(second, self.root)
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second/path.name).read_bytes())
            for name in ('define-workflow', 'execute-workflow'):
                with zipfile.ZipFile(first/f'{name}-v0.1.0.zip') as archive:
                    self.assertEqual(archive.read(f'{name}/SKILL.md'), (self.root/f'skills/{name}/SKILL.md').read_bytes())
                    self.assertEqual(json.loads(archive.read(f'{name}/RELEASE.json'))['commit'], selected['head'])
                    self.assertIn(f'{name}/scripts/workflow.py', archive.namelist())
            checksums = json.loads((first/'SHA256SUMS.json').read_text())
            self.assertEqual(len(checksums), 5)
            self.assertIn('package skills', (first/'CHANGELOG.md').read_text())
            self.assertIn('https://github.com/tclasen/sparkle/tree/v0.1.0', (first/'RELEASE_NOTES.md').read_text())
            self.git('tag', 'v0.1.0')
            third = Path(temp)/'third'
            r.build(third, self.root)
            self.assertEqual((first/'SHA256SUMS.json').read_bytes(), (third/'SHA256SUMS.json').read_bytes())
            self.commit('fix: correct package')
            fourth = Path(temp)/'fourth'
            r.build(fourth, self.root)
            log = (fourth/'CHANGELOG.md').read_text()
            self.assertLess(log.index('## v0.1.1'), log.index('## v0.1.0'))

    def test_dirty_or_stale_packages_rejected(self):
        self.package_fixture()
        (self.root/'skills/define-workflow/scripts/workflow.py').write_text('stale')
        with self.assertRaisesRegex(ValueError, 'commit tracked'):
            r.build(self.root/'dist', self.root)
        self.commit('fix: change one copy')
        with self.assertRaisesRegex(ValueError, 'stale'):
            r.build(self.root/'dist', self.root)

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
