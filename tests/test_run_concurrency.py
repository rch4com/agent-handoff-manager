"""Real subprocess contention and real worktrees; no host agent or network needed."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

import test_runs as fixtures

h, RESULT = fixtures.h, fixtures.RESULT


class RunConcurrencyTests(unittest.TestCase):
    setUp = fixtures.RunTests.setUp
    start = fixtures.RunTests.start

    def spawn(self, *args):
        return subprocess.Popen([sys.executable, '-I', h.__file__, '--repo', str(self.root), *args],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')

    def collect(self, processes):
        results = []
        for p in processes:
            out, err = p.communicate(timeout=60)
            results.append((p.returncode, json.loads(out) if p.returncode == 0 else err))
        return results

    def start_args(self, key, instance='worker'):
        return ['run-start', self.session['id'], '--task', 'core', '--agent', 'other',
                '--agent-instance', instance, '--request-id', key]

    def result_file(self, name, body):
        path = self.root / name
        path.write_text(json.dumps(body), encoding='utf-8')
        return str(path)

    def test_parallel_starts_keep_all_distinct_workers_and_same_key_replays_once(self):
        results = self.collect([self.spawn(*self.start_args('key-' + str(i), 'worker-' + str(i))) for i in range(6)])
        self.assertTrue(all(code == 0 for code, _ in results), results)
        self.assertEqual(6, len({data['id'] for _, data in results}))
        replays = self.collect([self.spawn(*self.start_args('same-key')) for _ in range(6)])
        self.assertTrue(all(code == 0 for code, _ in replays), replays)
        self.assertEqual(1, len({data['id'] for _, data in replays}))
        self.assertEqual(7, len(h.list_runs(self.root)))

    def test_parallel_distinct_results_and_same_result_replays_are_preserved(self):
        runs = [self.start('run-' + str(i)) for i in range(6)]
        body = self.result_file('result.json', RESULT)
        results = self.collect([self.spawn('run-finish', run['id'], '--payload', body, '--request-id', 'finish') for run in runs])
        self.assertTrue(all(code == 0 for code, _ in results), results)
        replays = self.collect([self.spawn('run-finish', runs[0]['id'], '--payload', body, '--request-id', 'finish') for _ in range(4)])
        self.assertTrue(all(code == 0 for code, _ in replays), replays)
        self.assertTrue(all(data == results[0][1] for _, data in replays))
        self.assertTrue(all(item['state'] == 'completed' for item in h.list_runs(self.root)))

    def test_competing_final_results_never_overwrite_the_winner(self):
        run = self.start()
        results = self.collect([self.spawn('run-finish', run['id'], '--payload',
                    self.result_file('r' + str(i) + '.json', dict(RESULT, summary='worker ' + str(i))),
                    '--request-id', 'finish-' + str(i)) for i in range(6)])
        self.assertEqual(1, sum(code == 0 for code, _ in results), results)
        self.assertEqual(5, sum(code == 2 for code, _ in results), results)
        winner = next(data for code, data in results if code == 0)
        self.assertEqual(winner, h.read_run(self.root, run['id'])['result'])

    def test_source_update_and_start_capture_one_complete_revision(self):
        body = self.result_file('source.json', {'mission': 'new mission', 'next_action': 'new next'})
        processes = [self.spawn('write', '--payload', body, '--id', self.session['id'], '--expected-revision', '1'),
                     self.spawn(*self.start_args('racing-start'))]
        results = self.collect(processes)
        self.assertTrue(all(code == 0 for code, _ in results), results)
        snapshot = results[1][1]['source_snapshot']
        expected = {1: ('original', 'review'), 2: ('new mission', 'new next')}
        self.assertEqual(expected[snapshot['revision']], (snapshot['payload']['mission'], snapshot['payload']['next_action']))

    def test_source_archive_finish_and_start_can_race_without_losing_results(self):
        run = self.start()
        body = self.result_file('result.json', RESULT)
        results = self.collect([self.spawn('archive', self.session['id'], '--confirm'),
                               self.spawn('run-finish', run['id'], '--payload', body, '--request-id', 'finish'),
                               self.spawn(*self.start_args('another-start'))])
        self.assertTrue(all(code == 0 for code, _ in results), results)
        self.assertEqual('completed', h.read_run(self.root, run['id'])['state'])
        self.assertEqual(2, len(h.resume(self.root, self.session['id'])['runs']))
        self.assertTrue(h.doctor(self.root)['ok'])

    def test_all_worktrees_exposes_origins_and_rejects_conflicting_copies(self):
        def git(*args):
            subprocess.run(['git', '-C', str(self.root), '-c', 'user.email=a@a', '-c', 'user.name=a', *args],
                           check=True, capture_output=True)

        git('init', '-q')
        (self.root / 'app.py').write_text('base')
        git('add', 'app.py')
        git('commit', '-qm', 'base')
        other = self.root / '작업 tree'
        git('worktree', 'add', '-qb', 'other', str(other))
        run = self.start()
        shutil.copytree(self.root / '.handoffs', other / '.handoffs')
        h.finish_run(self.root, run['id'], RESULT, 'f')
        found = h.list_runs(self.root, all_worktrees=True)
        self.assertEqual(2, len(found))
        self.assertEqual({str(self.root.resolve()), str(other.resolve())}, {x['worktree_root'] for x in found})
        h.finish_run(other, run['id'], dict(RESULT, summary='conflicting branch result'), 'f')
        with self.assertRaisesRegex(h.HandoffError, 'Conflicting'):
            h.list_runs(self.root, all_worktrees=True)


if __name__ == '__main__':
    unittest.main()
