#!/usr/bin/env python3
"""Conservative, stdlib-only local handoff runtime (pilot; no host transcript access)."""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time

VERSION = '0.2.0-pilot'
ID_RE = re.compile(r'^\d{8}T\d{6}Z-[0-9a-f]{12}$')
AGENTS = {'claude-code', 'codex', 'opencode', 'antigravity', 'copilot', 'other'}
STATUS = {'open', 'blocked', 'done'}
VALIDATION = {'passed', 'failed', 'not_run', 'unknown'}
KEY_RE = re.compile(r'(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?i:bearer)\s+[A-Za-z0-9._~-]{16,}|(?i:(?:api[_-]?key|access[_-]?token|secret|password))\s*[:=]\s*["\']?\S{8,})')
FIELDS = {'mission', 'acceptance_criteria', 'completed', 'in_progress', 'blocked', 'changed_files', 'decisions', 'failed_attempts', 'validation', 'next_action', 'agent', 'worktree', 'branch', 'head'}

class HandoffError(Exception):
    pass

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds').replace('+00:00', 'Z')

def ensure_repo(repo):
    root = Path(repo).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise HandoffError('Repository path is not a directory')
    return root

def home(root):
    dest = root / '.handoffs'
    if dest.is_symlink():
        raise HandoffError('Symlinked .handoffs is not allowed')
    return dest

def bucket(root, archived=False):
    base = home(root)
    target = base / ('archive' if archived else 'sessions')
    if target.is_symlink():
        raise HandoffError('Symlinked store bucket is not allowed')
    return target

def safe_dir(path):
    if path.is_symlink():
        raise HandoffError('Symlinked session directories are not allowed')
    if not path.is_dir():
        raise HandoffError('Session not found')
    return path

def git(root, *args):
    try:
        p = subprocess.run(['git', '-C', str(root), *args], capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=5, check=False)
        return p.stdout.strip() if p.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        return None

def sanitize_payload(raw):
    if not isinstance(raw, dict):
        raise HandoffError('Payload must be a JSON object')
    unknown = set(raw) - FIELDS
    if unknown:
        raise HandoffError('Unexpected payload fields: ' + ', '.join(sorted(unknown)))
    for key in ('mission', 'next_action'):
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise HandoffError(f'{key} requires nonempty text')
    agent = raw.get('agent', 'other')
    if agent not in AGENTS:
        raise HandoffError('Unknown agent')
    for key in ('acceptance_criteria', 'completed', 'in_progress', 'blocked', 'decisions', 'failed_attempts'):
        value = raw.get(key, [])
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            raise HandoffError(f'{key} must be a list of strings')
    for key in ('worktree', 'branch', 'head'):
        if key in raw and raw[key] is not None and not isinstance(raw[key], str):
            raise HandoffError(f'{key} must be text')
    changed = raw.get('changed_files', [])
    if not isinstance(changed, list) or any(not isinstance(x, dict) or not isinstance(x.get('path'), str) or not isinstance(x.get('owner'), str) for x in changed):
        raise HandoffError('changed_files must contain path and owner strings')
    for item in changed:
        p = item['path']
        if not p or p.startswith(('/', '\\')) or '\\' in p or any(part == '..' for part in p.split('/')) or re.match(r'^[A-Za-z]:', p):
            raise HandoffError('changed_files paths must be relative and non-traversing')
    validations = raw.get('validation', [])
    if not isinstance(validations, list) or any(not isinstance(v, dict) or v.get('result') not in VALIDATION or not isinstance(v.get('command'), str) or not isinstance(v.get('evidence', ''), str) for v in validations):
        raise HandoffError('validation must contain command and a supported result')
    serialized = json.dumps(raw, ensure_ascii=False)
    if KEY_RE.search(serialized):
        raise HandoffError('Potential credential detected; remove it before saving')
    if len(serialized.encode('utf-8')) > 256_000:
        raise HandoffError('Payload exceeds 256 KB')
    return raw

def atomic_json(path, obj):
    if path.is_symlink():
        raise HandoffError('Symlinked metadata is not allowed')
    fd, tmp = tempfile.mkstemp(prefix='.pending-', dir=str(path.parent))
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as stream:
            json.dump(obj, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

class StoreLock:
    def __init__(self, root):
        self.path = home(root) / '.write.lock'
        self.fd = None
    def __enter__(self):
        deadline = time.monotonic() + 4
        while True:
            try:
                self.fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.write(self.fd, (f'pid={os.getpid()} time={now()}\n').encode())
                os.fsync(self.fd)
                return self
            except FileExistsError:
                if time.monotonic() > deadline:
                    raise HandoffError('Store is locked; investigate .handoffs/.write.lock (never automatically delete)')
                time.sleep(.08)
    def __exit__(self, *_):
        if self.fd is not None:
            os.close(self.fd)
            self.path.unlink(missing_ok=True)

def init(root):
    home(root).mkdir(exist_ok=True)
    for a in ('sessions', 'archive'):
        bucket(root, a == 'archive').mkdir(exist_ok=True)

def read_record(path):
    safe_dir(path)
    file = path / 'session.json'
    if file.is_symlink():
        raise HandoffError('Symlinked metadata is not allowed')
    try:
        data = json.loads(file.read_text(encoding='utf-8'))
    except (OSError, ValueError) as e:
        raise HandoffError(f'Unreadable session record: {path.name}: {e}') from e
    if data.get('schema_version') != 1 or data.get('id') != path.name or not ID_RE.fullmatch(path.name) or not isinstance(data.get('revision'), int):
        raise HandoffError(f'Invalid session record: {path.name}')
    return data

def locate(root, identifier, archived=None):
    if identifier == 'latest':
        candidates = sorted((p for p in bucket(root).iterdir() if p.is_dir() and not p.is_symlink() and ID_RE.fullmatch(p.name)), reverse=True) if bucket(root).exists() else []
        if not candidates:
            raise HandoffError('No active sessions')
        identifier = candidates[0].name
    if not ID_RE.fullmatch(identifier):
        raise HandoffError('Invalid session id')
    options = ([archived] if archived is not None else [False, True])
    found = [bucket(root, flag) / identifier for flag in options if (bucket(root, flag) / identifier).exists()]
    if len(found) != 1:
        raise HandoffError('Session not found or duplicated')
    return safe_dir(found[0])

def project_identity(root):
    return hashlib.sha256(str(root).encode()).hexdigest()[:24]


def write(root, payload, identifier=None, expected_revision=None):
    raw = sanitize_payload(payload)
    init(root)
    with StoreLock(root):
        if identifier:
            path = locate(root, identifier, False)
            record = read_record(path)
            if expected_revision is None or expected_revision != record['revision']:
                raise HandoffError('Revision conflict: pass current --expected-revision')
            if record['status'] == 'archived':
                raise HandoffError('Archived session is read-only')
            revision = record['revision'] + 1
            created = record['created_at']
        else:
            identifier = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + secrets.token_hex(6)
            path = bucket(root) / identifier
            path.mkdir()  # no mode: Python>=3.13 on Windows turns 0o700 into an owner-only ACL that blocks other processes (sandboxed agents, git)
            revision, created = 1, now()
        identity = project_identity(root)
        record = {'schema_version': 1, 'writer_version': VERSION, 'id': identifier,
                  'project_id': identity, 'revision': revision, 'status': 'open',
                  'created_at': created, 'updated_at': now(),
                  'git_observation': {'branch': git(root, 'branch', '--show-current'), 'head': git(root, 'rev-parse', 'HEAD'), 'dirty': bool(git(root, 'status', '--porcelain')) if git(root, 'status', '--porcelain') is not None else None},
                  'payload': raw, 'claims_are_unverified': True}
        atomic_json(path / 'session.json', record)
        return record

def list_records(root, archived=False):
    directory = bucket(root, archived)
    return [read_record(p) for p in sorted(directory.iterdir()) if p.is_dir() and not p.is_symlink()] if directory.exists() else []

LIST_STATUS = ('open', 'archived', 'all')


def _day(value, name):
    try:
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
            raise ValueError
        return dt.date.fromisoformat(value).isoformat()
    except (ValueError, TypeError):
        raise HandoffError(f'{name} must be YYYY-MM-DD') from None


def worktree_roots(root):
    """Checkout roots of this repository (read-only `git worktree list`); just [root] outside Git."""
    out = git(root, 'worktree', 'list', '--porcelain', '-z')
    roots = [root]
    for field in (out or '').split('\0'):
        if field.startswith('worktree '):
            path = Path(field[len('worktree '):])
            if path.is_dir() and path.resolve() not in roots:
                roots.append(path.resolve())
    return roots


def list_filtered(root, status='open', agent=None, since=None, until=None, all_worktrees=False):
    if status not in LIST_STATUS:
        raise HandoffError('status must be one of: ' + ', '.join(LIST_STATUS))
    if agent is not None and agent not in AGENTS:
        raise HandoffError('Unknown agent')
    since = _day(since, 'since') if since else None
    until = _day(until, 'until') if until else None
    found = []
    for checkout in (worktree_roots(root) if all_worktrees else [root]):
        try:
            for archived in ((False,) if status == 'open' else (True,) if status == 'archived' else (False, True)):
                for record in list_records(checkout, archived):
                    if all_worktrees:
                        record = dict(record, worktree_root=str(checkout))
                    found.append(record)
        except HandoffError as exc:
            if checkout == root:
                raise
            print(f'WARNING: skipped worktree {checkout}: {exc}', file=sys.stderr)
    out = []
    for r in found:
        day = r['created_at'][:10]
        if agent and r['payload'].get('agent', 'other') != agent:
            continue
        if (since and day < since) or (until and day > until):
            continue
        out.append(r)
    return sorted(out, key=lambda r: (r['id'], r.get('worktree_root', '')))


def resume(root, identifier):
    record = read_record(locate(root, identifier))
    observed = {'branch': git(root, 'branch', '--show-current'), 'head': git(root, 'rev-parse', 'HEAD'), 'dirty': bool(git(root, 'status', '--porcelain')) if git(root, 'status', '--porcelain') is not None else None}
    differences = {k: {'saved': record['git_observation'].get(k), 'current': value} for k, value in observed.items() if value != record['git_observation'].get(k)}
    return {'session': record, 'current_git': observed, 'differences': differences, 'note': 'Read-only. Nothing from the payload has been executed; validation claims are not independently verified.'}

def transition(root, identifier, to_archive):
    init(root)
    with StoreLock(root):
        source = locate(root, identifier, archived=not to_archive)
        original = read_record(source)
        destination = bucket(root, to_archive) / identifier
        if destination.exists():
            raise HandoffError('Destination already exists')
        updated = dict(original, status='archived' if to_archive else 'open', revision=original['revision'] + 1, updated_at=now())
        atomic_json(source / 'session.json', updated)
        try:
            source.rename(destination)
        except OSError:
            atomic_json(source / 'session.json', original)
            raise
        return updated

LEGACY_NAME_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})-(\d{4})-.+\.md$')
AGENT_HINTS = (('claude', 'claude-code'), ('codex', 'codex'), ('opencode', 'opencode'), ('antigravity', 'antigravity'), ('copilot', 'copilot'))


def _section(text, number):
    m = re.search(rf'^## {number}\. .*$', text, re.M)
    if not m:
        return ''
    rest = text[m.end():]
    nxt = re.search(r'^## ', rest, re.M)
    return (rest[:nxt.start()] if nxt else rest).strip()


def _bad_rel_path(p):
    return not p or p.startswith(('/', '\\')) or '\\' in p or any(part == '..' for part in p.split('/')) or bool(re.match(r'^[A-Za-z]:', p))


def _bullets(section, marker, label):
    out = []
    for m in re.finditer(rf'^\s*[-*]\s*{marker}\s*(?:{label}:)?\s*(.+)$', section, re.M):
        item = m.group(1).strip()
        if item and not item.startswith(('<', '(nothing')):
            out.append(item)
    return out


def parse_legacy(text, name):
    """Best-effort parse of an aploe/claude-handoff-skill v1 document; None if it is not one."""
    title = re.search(r'^# Handoff:\s*(.+)$', text, re.M)
    if not title and 'HANDOFF-DOC v' not in text:
        return None

    def squash(value, limit=1000):
        return re.sub(r'\s+', ' ', value).strip()[:limit]

    mission = squash(_section(text, 1)) or (title.group(1).strip() if title else name)
    next_action = squash(_section(text, 3)) or 'UNKNOWN: see legacy_import.original_text'
    who = re.search(r'Original Agent:\*{0,2}\s*(.+?)(?:\s*·|$)', text, re.M)
    agent = 'other'
    for hint, value in AGENT_HINTS:
        if who and hint in who.group(1).lower():
            agent = value
            break
    state = _section(text, 2)
    changed = []
    for line in _section(text, 5).splitlines():
        cells = [c.strip().strip('`') for c in line.strip().strip('|').split('|')]
        if line.strip().startswith('|') and len(cells) >= 2 and cells[0].lower() != 'file' and not set(cells[0]) <= set('-: '):
            if not _bad_rel_path(cells[0]):
                changed.append({'path': cells[0], 'owner': agent})
    return {'agent': agent, 'mission': mission, 'next_action': next_action,
            'completed': _bullets(state, '✅', 'Done'), 'in_progress': _bullets(state, '🔄', 'In Progress'),
            'blocked': _bullets(state, '⏸️?', 'Blocked'), 'changed_files': changed}


def _legacy_created(name, path):
    m = LEGACY_NAME_RE.match(name)
    if m:
        y, mo, d, hm = int(m[1]), int(m[2]), int(m[3]), m[4]
        try:  # upstream stamps are local time without zone: conversion uses this machine's zone (approximate)
            return dt.datetime(y, mo, d, int(hm[:2]), int(hm[2:])).astimezone(dt.timezone.utc)
        except ValueError:
            pass
    return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc)


def import_legacy(root, dry_run=False):
    """Copy legacy .handoffs/*.md into session records. Never modifies, moves or deletes the originals."""
    result = {'imported': [], 'would_import': [], 'skipped': []}
    base = home(root)
    if not base.is_dir():
        return result
    if not dry_run:
        init(root)
    known = set()
    for archived in (False, True):
        directory = bucket(root, archived)
        if directory.is_dir():
            for d in directory.iterdir():
                try:
                    known.add(read_record(d).get('legacy_import', {}).get('source_sha256'))
                except HandoffError:
                    pass
    lock = None if dry_run else StoreLock(root)
    if lock:
        lock.__enter__()
    try:
        for path in sorted(base.glob('*.md')):
            def skip(reason, path=path):
                result['skipped'].append({'file': path.name, 'reason': reason})
            if path.is_symlink():
                skip('symlink')
                continue
            if not path.is_file():
                continue
            if path.stat().st_size > 256_000:
                skip('too_large')
                continue
            raw = path.read_bytes()
            try:
                text = raw.decode('utf-8')
            except UnicodeDecodeError:
                skip('not_utf8')
                continue
            parsed = parse_legacy(text, path.name)
            if parsed is None:
                skip('not_a_handoff_doc')
                continue
            if KEY_RE.search(text):
                skip('possible_credential')
                continue
            digest = hashlib.sha256(raw).hexdigest()
            if digest in known:
                skip('already_imported')
                continue
            created = _legacy_created(path.name, path)
            identifier = created.strftime('%Y%m%dT%H%M%SZ') + '-' + digest[:12]
            entry = {'file': path.name, 'id': identifier}
            if dry_run:
                result['would_import'].append(entry)
                continue
            stamp = now()
            record = {'schema_version': 1, 'writer_version': VERSION, 'id': identifier,
                      'project_id': project_identity(root), 'revision': 1, 'status': 'open',
                      'created_at': created.isoformat(timespec='seconds').replace('+00:00', 'Z'), 'updated_at': stamp,
                      'git_observation': {'branch': None, 'head': None, 'dirty': None},
                      'payload': sanitize_payload(parsed), 'claims_are_unverified': True,
                      'legacy_import': {'format': 'claude-handoff-skill v1', 'source_file': path.name,
                                        'source_sha256': digest, 'imported_at': stamp,
                                        'created_at_is_approximate': True, 'original_text': text}}
            target = bucket(root) / identifier
            try:
                target.mkdir()
            except FileExistsError:
                skip('id_collision')
                continue
            try:
                atomic_json(target / 'session.json', record)
            except BaseException:
                shutil.rmtree(target, ignore_errors=True)
                raise
            known.add(digest)
            result['imported'].append(entry)
    finally:
        if lock:
            lock.__exit__()
    return result


def doctor(root):
    issues = []
    base = home(root)
    if not base.exists():
        return {'ok': False, 'issues': ['Store not initialized']}
    if (base / '.write.lock').exists():
        issues.append('Outstanding writer lock; investigate before removing')
    for archived in (False, True):
        directory = bucket(root, archived)
        if not directory.exists():
            issues.append(f'Missing directory {directory.name}')
            continue
        for p in directory.iterdir():
            if p.name.startswith('.pending-') or p.is_symlink():
                issues.append(f'Unexpected path: {p.name}')
            elif p.is_dir():
                try:
                    rec = read_record(p)
                    if (rec['status'] == 'archived') != archived:
                        issues.append(f'Status/location mismatch (possible interrupted transition): {p.name}')
                    if (bucket(root, not archived) / p.name).exists():
                        issues.append(f'Duplicate session id: {p.name}')
                except HandoffError as exc:
                    issues.append(str(exc))
    return {'ok': not issues, 'issues': issues}

def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp949/cp1252; output is JSON with ensure_ascii=False
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', default='.')
    parser.add_argument('--version', action='version', version=f'agent-handoff-manager core {VERSION}')
    commands = parser.add_subparsers(dest='cmd', required=True)
    commands.add_parser('init')
    wr = commands.add_parser('write'); wr.add_argument('--payload', required=True, help='Local JSON payload file; never executes embedded commands'); wr.add_argument('--id'); wr.add_argument('--expected-revision', type=int)
    ls = commands.add_parser('list')
    ls.add_argument('--archived', action='store_true', help='Alias for --status archived')
    ls.add_argument('--status', choices=LIST_STATUS)
    ls.add_argument('--agent', choices=sorted(AGENTS))
    ls.add_argument('--since', metavar='YYYY-MM-DD', help='created_at (UTC date) >= value')
    ls.add_argument('--until', metavar='YYYY-MM-DD', help='created_at (UTC date) <= value')
    ls.add_argument('--all-worktrees', action='store_true', help='Also read the stores of other git worktrees (read-only)')
    re = commands.add_parser('resume'); re.add_argument('id')
    ar = commands.add_parser('archive'); ar.add_argument('id'); ar.add_argument('--confirm', action='store_true')
    rs = commands.add_parser('restore'); rs.add_argument('id'); rs.add_argument('--confirm', action='store_true')
    commands.add_parser('doctor')
    il = commands.add_parser('import-legacy')
    il.add_argument('--dry-run', action='store_true', help='Report what would be imported; write nothing')
    args = parser.parse_args(argv)
    try:
        root = ensure_repo(args.repo)
        if args.cmd == 'init':
            init(root); result = {'initialized': str(home(root))}
        elif args.cmd == 'write':
            source = Path(args.payload)
            if source.is_symlink() or not source.is_file() or source.stat().st_size > 256_000:
                raise HandoffError('Payload must be a regular non-symlink file <=256 KB')
            result = write(root, json.loads(source.read_text(encoding='utf-8')), args.id, args.expected_revision)
        elif args.cmd == 'list':
            if args.archived and args.status not in (None, 'archived'):
                raise HandoffError('--archived conflicts with --status')
            result = list_filtered(root, 'archived' if args.archived else (args.status or 'open'), args.agent, args.since, args.until, args.all_worktrees)
        elif args.cmd == 'resume': result = resume(root, args.id)
        elif args.cmd == 'doctor': result = doctor(root)
        elif args.cmd == 'import-legacy': result = import_legacy(root, args.dry_run)
        else:
            if not args.confirm:
                raise HandoffError('Explicit --confirm required')
            result = transition(root, args.id, args.cmd == 'archive')
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if args.cmd != 'doctor' or result['ok'] else 1
    except (HandoffError, OSError, json.JSONDecodeError, ValueError) as exc:
        print(f'HANDOFF_ERROR: {exc}', file=sys.stderr)
        return 2

if __name__ == '__main__':
    raise SystemExit(main())
