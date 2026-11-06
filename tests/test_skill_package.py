"""Clean-copy test: only the skill directory is copied (what gh skill / npx skills do)."""
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / 'skills' / 'agent-handoff-manager'
PAYLOAD = {'agent': 'copilot', 'mission': '미션 한글 ✓', 'next_action': 'Run tests',
           'failed_attempts': ['tried X: failed because Y']}


class CleanCopyTests(unittest.TestCase):
    def test_installed_copy_runs_full_lifecycle_in_non_ascii_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            installed = tmp / '설치 경로 with space' / '.agents' / 'skills' / 'agent-handoff-manager'
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns('__pycache__'))
            repo = tmp / '프로젝트 repo'
            repo.mkdir()
            payload = tmp / 'p.json'
            payload.write_text(json.dumps(PAYLOAD, ensure_ascii=False), encoding='utf-8')

            def run(*args, code=0):
                r = subprocess.run([sys.executable, '-I', str(installed / 'scripts' / 'handoff.py'),
                                    '--repo', str(repo), *args],
                                   capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(code, r.returncode, r.stderr)
                return r.stdout

            run('init')
            rec = json.loads(run('write', '--payload', str(payload)))
            self.assertEqual(1, len(json.loads(run('list'))))
            got = json.loads(run('resume', 'latest'))
            self.assertEqual(PAYLOAD['mission'], got['session']['payload']['mission'])
            run('archive', rec['id'], '--confirm')
            self.assertEqual([], json.loads(run('list')))
            run('restore', rec['id'], '--confirm')
            self.assertTrue(json.loads(run('doctor'))['ok'])
            self.assertIn('0.2.0', run('--version') or '')  # argparse prints version to stdout on 3.4+

    def test_skill_md_matches_directory_and_is_self_contained(self):
        text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('\nname: agent-handoff-manager\n', text)
        self.assertNotIn('../', text)


if __name__ == '__main__':
    unittest.main()
