"""Regressions from the 2026-11-13 repository audit; use only fake credentials."""
import contextlib
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skills' / 'agent-handoff-manager' / 'scripts'))
import handoff


class AuditRegressionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.payload = {'mission': 'audit', 'next_action': 'review'}

    def test_latest_is_rejected_for_moves_without_changing_records(self):
        rec = handoff.write(self.root, self.payload)
        original = handoff.locate(self.root, rec['id']) / 'session.json'
        before = original.read_bytes()
        for command in ('archive', 'restore'):
            for mode in ('--dry-run', '--confirm'):
                with self.subTest(command=command, mode=mode):
                    stderr = io.StringIO()
                    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
                        code = handoff.main(['--repo', str(self.root), command, 'latest', mode])
                    self.assertEqual(2, code)
                    self.assertIn('Invalid session id', stderr.getvalue())
                    self.assertEqual(before, original.read_bytes())
                    self.assertTrue(handoff.doctor(self.root)['ok'])

    def test_quoted_credentials_and_multiline_tokens_are_not_saved(self):
        fake = 'FAKE_AUDIT_CREDENTIAL_123'
        texts = [json.dumps({key: fake}) for key in ('password', 'api_key', 'access_token', 'secret')]
        texts += ["'password': '" + fake + "'", 'Authorization: Bearer\n' + fake]
        for text in texts:
            with self.subTest(text=text):
                with self.assertRaisesRegex(handoff.HandoffError, 'credential') as caught:
                    handoff.write(self.root, dict(self.payload, next_action=text))
                self.assertNotIn(fake, str(caught.exception))
        self.assertEqual([], handoff.list_records(self.root))

    def test_invalid_records_are_reported_and_never_rewritten(self):
        rec = handoff.write(self.root, self.payload)
        path = handoff.locate(self.root, rec['id']) / 'session.json'
        good = json.loads(path.read_text(encoding='utf-8'))
        invalid = [[], None]
        for key in ('payload', 'git_observation', 'status', 'created_at', 'updated_at',
                    'writer_version', 'project_id', 'claims_are_unverified'):
            data = copy.deepcopy(good)
            del data[key]
            invalid.append(data)
        for key, value in [('revision', True), ('revision', 0), ('status', []),
                           ('created_at', 'yesterday'), ('payload', []),
                           ('git_observation', {'branch': [], 'head': None, 'dirty': None})]:
            invalid.append(dict(good, **{key: value}))
        for field, value in [('agent', []), ('changed_files', [{'path': '../outside', 'owner': 'other'}]),
                             ('validation', [{'command': 'check', 'result': []}])]:
            invalid.append(dict(good, payload=dict(self.payload, **{field: value})))
        for data in invalid:
            with self.subTest(data=data):
                path.write_text(json.dumps(data), encoding='utf-8')
                before = path.read_bytes()
                report = handoff.doctor(self.root)
                self.assertFalse(report['ok'])
                self.assertTrue(any('Invalid session record' in x for x in report['issues']))
                with self.assertRaises(handoff.HandoffError):
                    handoff.resume(self.root, rec['id'])
                self.assertEqual(before, path.read_bytes())

    def test_structured_credential_assignments_in_nested_objects_are_not_saved(self):
        fake = 'FAKE_AUDIT_CREDENTIAL_123'
        for field, item in [('validation', {'command': 'check', 'result': 'not_run'}),
                            ('changed_files', {'path': 'app.txt', 'owner': 'other'})]:
            with self.subTest(field=field):
                with self.assertRaisesRegex(handoff.HandoffError, 'credential'):
                    handoff.write(self.root, dict(self.payload, **{field: [dict(item, password=fake)]}))
        self.assertEqual([], handoff.list_records(self.root))

    def test_v1_record_without_depth_and_with_unknown_envelope_field_still_reads(self):
        rec = handoff.write(self.root, self.payload)
        path = handoff.locate(self.root, rec['id']) / 'session.json'
        data = json.loads(path.read_text(encoding='utf-8'))
        del data['depth']
        data['future_field'] = 'preserve'
        path.write_text(json.dumps(data), encoding='utf-8')
        self.assertEqual('preserve', handoff.resume(self.root, rec['id'])['session']['future_field'])
        self.assertTrue(handoff.doctor(self.root)['ok'])

    def test_dirty_tree_always_warns_even_when_dirty_was_saved(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=a@a',
                            '-c', 'user.name=a', *args], check=True, capture_output=True)

        git('init', '-q')
        source = self.root / 'app.txt'
        source.write_text('base', encoding='utf-8')
        git('add', 'app.txt')
        git('commit', '-qm', 'base')
        source.write_text('first edit', encoding='utf-8')
        rec = handoff.write(self.root, self.payload)
        source.write_text('second edit', encoding='utf-8')
        result = handoff.resume(self.root, rec['id'])
        self.assertEqual({}, result['differences'])
        self.assertTrue(any('uncommitted' in x and 'not verified' in x for x in result['warnings']))


if __name__ == '__main__':
    unittest.main()
