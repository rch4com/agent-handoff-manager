import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "skills" / "agent-handoff-manager" / "scripts"))
import handoff

PAYLOAD = {'agent': 'codex', 'mission': 'Implement a small feature', 'next_action': 'Review tests',
           'acceptance_criteria': ['Tests pass'], 'validation': [{'command': 'python -m unittest', 'result': 'not_run', 'evidence': ''}],
           'changed_files': [{'path': 'src/example.py', 'owner': 'codex'}]}

class HandoffRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        handoff.init(self.root)

    def test_create_list_resume_archive_restore(self):
        item = handoff.write(self.root, PAYLOAD)
        self.assertEqual(1, item['revision'])
        self.assertEqual(1, len(handoff.list_records(self.root)))
        observed = handoff.resume(self.root, item['id'])
        self.assertIn('Read-only', observed['note'])
        archived = handoff.transition(self.root, item['id'], True)
        self.assertEqual('archived', archived['status'])
        self.assertEqual([], handoff.list_records(self.root))
        self.assertEqual(1, len(handoff.list_records(self.root, True)))
        handoff.transition(self.root, item['id'], False)
        self.assertEqual(3, handoff.read_record(handoff.locate(self.root, item['id']))['revision'])
        self.assertTrue(handoff.doctor(self.root)['ok'])

    def test_optimistic_revision_conflicts(self):
        item = handoff.write(self.root, PAYLOAD)
        with self.assertRaisesRegex(handoff.HandoffError, 'Revision conflict'):
            handoff.write(self.root, PAYLOAD, item['id'], 0)
        self.assertEqual(2, handoff.write(self.root, PAYLOAD, item['id'], 1)['revision'])

    def test_credentials_and_paths_are_blocked(self):
        for body in [dict(PAYLOAD, next_action='sk-' + 'X'*28),
                     dict(PAYLOAD, changed_files=[{'path': '../private', 'owner': 'codex'}]),
                     dict(PAYLOAD, mystery=1)]:
            with self.assertRaises(handoff.HandoffError):
                handoff.write(self.root, body)
        self.assertEqual([], handoff.list_records(self.root))

    def test_doctor_detects_interrupted_archive(self):
        item = handoff.write(self.root, PAYLOAD)
        path = handoff.locate(self.root, item['id'])
        record = handoff.read_record(path)
        record['status'] = 'archived'
        handoff.atomic_json(path / 'session.json', record)
        self.assertFalse(handoff.doctor(self.root)['ok'])

    def test_session_dir_created_without_restrictive_mode(self):
        # Regression R-001: mkdir(mode=0o700) gives owner-only ACL on Windows py>=3.13; sandboxed hosts could not read it.
        from unittest import mock
        real = Path.mkdir
        modes = []
        def spy(self, *a, **k):
            modes.append(k.get('mode', a[0] if a else None))
            return real(self, *a, **k)
        with mock.patch.object(Path, 'mkdir', spy):
            handoff.write(self.root, PAYLOAD)
        self.assertNotIn(0o700, modes)

    def test_symlink_bucket_rejected(self):
        with tempfile.TemporaryDirectory() as other:
            (self.root / '.handoffs' / 'sessions').rename(self.root / '.handoffs' / 'sessions-safe')
            try:
                (self.root / '.handoffs' / 'sessions').symlink_to(other, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest('Symlink creation unavailable')
            with self.assertRaises(handoff.HandoffError):
                handoff.write(self.root, PAYLOAD)

    def test_cli_requires_confirm_and_does_not_run_payload(self):
        path = self.root / 'payload.json'
        path.write_text(json.dumps(PAYLOAD), encoding='utf-8')
        script = str(Path(handoff.__file__).resolve())
        base = [sys.executable, script, '--repo', str(self.root)]
        r = subprocess.run(base + ['write', '--payload', str(path)], capture_output=True, text=True)
        self.assertEqual(0, r.returncode, r.stderr)
        identifier = json.loads(r.stdout)['id']
        r = subprocess.run(base + ['archive', identifier], capture_output=True, text=True)
        self.assertEqual(2, r.returncode)
        self.assertTrue(handoff.locate(self.root, identifier).exists())

if __name__ == '__main__':
    unittest.main()
