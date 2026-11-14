"""Execution/result contract; all commands and validation evidence are untrusted data."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'skills' / 'agent-handoff-manager' / 'scripts'))
import handoff as h

RESULT = {'outcome': 'completed', 'summary': 'implemented', 'validation': [
    {'command': 'python -m unittest', 'result': 'passed', 'evidence': 'example claim, not verified'}],
    'changed_files': [{'path': 'app.py', 'owner': 'other'}], 'commits': ['a' * 40], 'remaining_work': []}


class RunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='인계 runs ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.session = h.write(self.root, {'mission': 'original', 'next_action': 'review'})

    def start(self, key='start-1', task='core', **extra):
        return h.start_run(self.root, self.session['id'], task, 'codex', 'codex-worker-1', key, **extra)

    def test_lifecycle_and_resume_links_do_not_change_session_or_application(self):
        source = h.locate(self.root, self.session['id']) / 'session.json'
        before = source.read_bytes()
        app = self.root / 'app.py'
        app.write_text('original', encoding='utf-8')
        official = self.root / 'AGENT_HANDOFF.md'
        official.write_text('verified official state', encoding='utf-8')
        run = self.start()
        self.assertEqual('in_progress', h.list_runs(self.root)[0]['state'])
        result = h.finish_run(self.root, run['id'], RESULT, 'finish-1')
        self.assertTrue(result['claims_are_unverified'])
        self.assertEqual('completed', h.list_runs(self.root)[0]['state'])
        self.assertEqual(run['id'], h.resume(self.root, self.session['id'])['runs'][0]['run']['id'])
        self.assertEqual(before, source.read_bytes())
        self.assertEqual('original', app.read_text())
        self.assertEqual('verified official state', official.read_text())
        self.assertTrue(h.doctor(self.root)['ok'])

    def test_snapshot_survives_source_update_archive_restore(self):
        run = self.start()
        h.write(self.root, {'mission': 'updated', 'next_action': 'new'}, self.session['id'], 1)
        h.transition(self.root, self.session['id'], True)
        h.finish_run(self.root, run['id'], RESULT, 'finish-1')
        item = h.list_runs(self.root)[0]
        self.assertEqual('original', item['run']['source_snapshot']['payload']['mission'])
        report = h.resume(self.root, self.session['id'])
        self.assertTrue(any('different session content' in w for w in report['warnings']))
        h.transition(self.root, self.session['id'], False)
        self.assertEqual('completed', h.list_runs(self.root)[0]['state'])

    def test_start_replay_preserves_original_snapshot_and_rejects_changed_arguments(self):
        run = self.start()
        h.write(self.root, {'mission': 'new', 'next_action': 'new'}, self.session['id'], 1)
        self.assertEqual(run, self.start())
        with self.assertRaisesRegex(h.HandoffError, 'request'):
            self.start(task='different')
        self.assertEqual(1, len(h.list_runs(self.root)))

    def test_finish_replay_never_rewrites_and_conflicting_result_is_rejected(self):
        run = self.start()
        result = h.finish_run(self.root, run['id'], RESULT, 'finish-1')
        path = self.root / '.handoffs/runs' / run['id'] / 'result.json'
        before = path.read_bytes()
        self.assertEqual(result, h.finish_run(self.root, run['id'], RESULT, 'finish-1'))
        for body, key in [(dict(RESULT, summary='changed'), 'finish-1'), (RESULT, 'finish-2')]:
            with self.assertRaisesRegex(h.HandoffError, 'immutable'):
                h.finish_run(self.root, run['id'], body, key)
        self.assertEqual(before, path.read_bytes())

    def test_retry_lineage_and_explicit_integration_selection_remain_claims(self):
        first = self.start()
        h.finish_run(self.root, first['id'], dict(RESULT, outcome='failed'), 'f1')
        retry = self.start('retry', supersedes=first['id'])
        h.finish_run(self.root, retry['id'], RESULT, 'f2')
        integration = self.start('integrate', task='integration')
        integrated = h.finish_run(self.root, integration['id'], dict(RESULT, selected_runs=[retry['id']]), 'f3')
        self.assertEqual([retry['id']], integrated['payload']['selected_runs'])
        self.assertEqual(first['id'], retry['supersedes'])
        self.assertFalse(h.resume(self.root, self.session['id'])['session_claims_are_official'])
        with self.assertRaises(h.HandoffError):
            self.start('bad-retry', task='other', supersedes=first['id'])

    def test_selection_rejects_self_unsubmitted_duplicates_and_other_session(self):
        run = self.start()
        other = h.write(self.root, {'mission': 'other', 'next_action': 'read'})
        foreign = h.start_run(self.root, other['id'], 'core', 'other', 'worker', 'foreign')
        h.finish_run(self.root, foreign['id'], RESULT, 'f')
        pending = self.start('pending')
        for selected in ([run['id']], [pending['id']], [foreign['id']], [foreign['id'], foreign['id']]):
            with self.subTest(selected=selected), self.assertRaises(h.HandoffError):
                h.finish_run(self.root, run['id'], dict(RESULT, selected_runs=selected), 'invalid')

    def test_secret_traversal_and_malformed_result_are_rejected_before_writing(self):
        with self.assertRaises(h.HandoffError):
            self.start(key='../outside')
        with self.assertRaises(h.HandoffError):
            self.start(task='password=FAKE_CREDENTIAL_123')
        run = self.start()
        bad = [[], dict(RESULT, outcome=[]), dict(RESULT, summary='password=FAKE_CREDENTIAL_123'),
               dict(RESULT, commits=['not-a-sha']), dict(RESULT, unexpected=True),
               dict(RESULT, changed_files=[{'path': '../outside', 'owner': 'other'}])]
        for body in bad:
            with self.subTest(body=body), self.assertRaises(h.HandoffError):
                h.finish_run(self.root, run['id'], body, 'bad')
        self.assertEqual('in_progress', h.list_runs(self.root)[0]['state'])

    def test_doctor_reports_tampering_and_interrupted_publication_without_repair(self):
        run = self.start()
        path = self.root / '.handoffs/runs' / run['id'] / 'run.json'
        good = json.loads(path.read_text(encoding='utf-8'))
        for data in ([], dict(good, source_payload_sha256='0' * 64), dict(good, source_revision=99)):
            path.write_text(json.dumps(data), encoding='utf-8')
            before = path.read_bytes()
            self.assertFalse(h.doctor(self.root)['ok'])
            self.assertEqual(before, path.read_bytes())
        path.write_text(json.dumps(good), encoding='utf-8')
        with mock.patch.object(h, 'atomic_json', side_effect=OSError('simulated disk failure')):
            with self.assertRaises(OSError):
                h.finish_run(self.root, run['id'], RESULT, 'f')
        self.assertEqual('in_progress', h.list_runs(self.root)[0]['state'])
        h.finish_run(self.root, run['id'], RESULT, 'f')
        (path.parent / '.pending-test').write_text('partial')
        self.assertFalse(h.doctor(self.root)['ok'])

    def test_old_store_read_does_not_create_runs_directory(self):
        before = sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*'))
        self.assertEqual([], h.list_runs(self.root))
        h.resume(self.root, self.session['id'])
        h.doctor(self.root)
        self.assertEqual(before, sorted(str(p.relative_to(self.root)) for p in self.root.rglob('*')))

    def test_symlinked_runs_bucket_is_rejected(self):
        with tempfile.TemporaryDirectory() as outside:
            try:
                (self.root / '.handoffs/runs').symlink_to(outside, target_is_directory=True)
            except OSError:
                self.skipTest('symlink creation unavailable')
            with self.assertRaises(h.HandoffError):
                self.start()
            self.assertFalse(h.doctor(self.root)['ok'])

    def test_start_is_not_visible_until_its_complete_record_is_published(self):
        real = h.atomic_json
        observations = []

        def during_write(path, record):
            if path.name == 'run.json':
                observations.append(h.list_runs(self.root))
            real(path, record)

        with mock.patch.object(h, 'atomic_json', side_effect=during_write):
            self.start()
        self.assertEqual([[]], observations)
        self.assertEqual(1, len(h.list_runs(self.root)))

    def test_interrupted_start_is_diagnosed_but_does_not_block_new_runs(self):
        with mock.patch.object(h, 'atomic_json', side_effect=OSError('interrupted before publication')):
            with self.assertRaises(OSError):
                self.start()
        self.assertEqual([], h.list_runs(self.root))
        self.assertFalse(h.doctor(self.root)['ok'])
        self.start('retry-after-interruption')
        self.assertEqual(1, len(h.list_runs(self.root)))

    def test_resume_warns_about_missing_selected_run_and_retry_predecessor(self):
        first = self.start()
        h.finish_run(self.root, first['id'], RESULT, 'f1')
        retry = self.start('retry', supersedes=first['id'])
        integration = self.start('integration', task='integration')
        h.finish_run(self.root, integration['id'], dict(RESULT, selected_runs=[first['id']]), 'f2')
        original = self.root / '.handoffs/runs' / first['id']
        original.rename(self.root / 'unmerged-execution')
        warnings = h.resume(self.root, self.session['id'])['warnings']
        for run in (retry, integration):
            self.assertTrue(any(run['id'] in w and 'reference' in w for w in warnings), warnings)
        self.assertFalse(h.doctor(self.root)['ok'])

    def test_result_validation_is_inert_and_records_the_actual_dirty_head(self):
        def git(*args):
            return subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=a@a', '-c', 'user.name=a',
                                   *args], check=True, capture_output=True, text=True).stdout.strip()

        git('init', '-qb', 'main')
        app = self.root / 'app.py'
        app.write_text('base')
        git('add', 'app.py')
        git('commit', '-qm', 'base')
        run = self.start()
        app.write_text('changed')
        canary = self.root / 'MUST_NOT_EXECUTE'
        payload = dict(RESULT, validation=[{'command': 'python -c "open(\'MUST_NOT_EXECUTE\',\'w\')"',
                                           'result': 'passed', 'evidence': 'untrusted claim'}])
        result = h.finish_run(self.root, run['id'], payload, 'f')
        self.assertEqual(git('rev-parse', 'HEAD'), result['git_observation']['head'])
        self.assertTrue(result['git_observation']['dirty'])
        self.assertTrue(result['claims_are_unverified'])
        self.assertFalse(canary.exists())

    def test_persisted_result_validation_is_fail_closed(self):
        run = self.start()
        h.finish_run(self.root, run['id'], RESULT, 'f')
        path = self.root / '.handoffs/runs' / run['id'] / 'result.json'
        good = json.loads(path.read_text(encoding='utf-8'))
        for data in ([], dict(good, schema_version=2), dict(good, run_id='wrong'),
                     dict(good, payload=dict(RESULT, summary='password=FAKE_CREDENTIAL_123'))):
            path.write_text(json.dumps(data), encoding='utf-8')
            with self.assertRaises(h.HandoffError):
                h.list_runs(self.root)
            self.assertFalse(h.doctor(self.root)['ok'])

    def test_symlinked_execution_and_result_are_not_followed(self):
        run = self.start()
        path = self.root / '.handoffs/runs' / run['id']
        outside = self.root / 'outside.json'
        outside.write_text('{}', encoding='utf-8')
        try:
            (path / 'result.json').symlink_to(outside)
        except OSError:
            self.skipTest('symlink creation unavailable')
        with self.assertRaises(h.HandoffError):
            h.finish_run(self.root, run['id'], RESULT, 'f')
        self.assertEqual('{}', outside.read_text())
        (path / 'result.json').unlink()
        relocated = self.root / 'relocated-run'
        path.rename(relocated)
        path.symlink_to(relocated, target_is_directory=True)
        with self.assertRaises(h.HandoffError):
            h.list_runs(self.root)
        self.assertFalse(h.doctor(self.root)['ok'])

    def test_pretty_printed_size_limit_is_checked_before_publication(self):
        wide = {'command': 'check', 'result': 'not_run', 'evidence': '', 'details': [0] * 80000}
        run = self.start()
        with self.assertRaisesRegex(h.HandoffError, '1 MB'):
            h.finish_run(self.root, run['id'], dict(RESULT, validation=[wide]), 'too-wide')
        self.assertIsNone(h.read_run(self.root, run['id'])['result'])
        h.write(self.root, {'mission': 'wide', 'next_action': 'review', 'validation': [wide]}, self.session['id'], 1)
        with self.assertRaisesRegex(h.HandoffError, '1 MB'):
            self.start('too-wide-start')
        self.assertEqual(1, len(h.list_runs(self.root)))


if __name__ == '__main__':
    unittest.main()
