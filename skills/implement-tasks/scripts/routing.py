#!/usr/bin/env python3
"""Local editor and Runner interface for a project's Harness Pool & Routing."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import secrets
import subprocess
import sys
import tempfile
import threading
import webbrowser
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from routing_catalog import detected_family, model_ids
from routing_runtime import Runtime, pair


CONFIG = Path('.agents/implement-tasks-routing.json')
POLICY = Path('.agents/implement-tasks-auto-merge.md')
HEADING = '## Harness Pool & Routing'
ASSETS = Path(__file__).with_name('routing_editor')
HARNESSES = ('codex', 'claude', 'agy', 'kimi', 'opencode', 'gemini', 'cursor', 'copilot', 'grok', 'pi')
EFFORTS = ('default', 'low', 'medium', 'high', 'xhigh', 'max')
ROLES = ('both', 'worker', 'reviewer')


def default_config():
    return {
        'version': 1,
        'harnesses': [],
        'pool': [],
        'prefer_independent_reviewer': True,
        'rules': [
            {'name': 'High-risk / architectural',
             'description': 'Security, migrations, concurrency, and cross-cutting or high-risk changes.',
             'candidates': []},
            {'name': 'Typical / mechanical',
             'description': 'Routine features, bug fixes, tests, and small mechanical changes.',
             'candidates': []},
        ],
    }


def require(condition, message):
    if not condition:
        raise ValueError(message)


def line(value):
    return isinstance(value, str) and bool(value.strip()) and not any(ord(char) < 32 for char in value)


def model_id(value):
    return value is None or line(value)


def validate(config):
    require(isinstance(config, dict) and type(config.get('version')) is int and config['version'] == 1,
            'Unsupported routing configuration version.')
    require(isinstance(config.get('pool'), list) and isinstance(config.get('rules'), list),
            'Routing requires a pool and an ordered list of rules.')
    harnesses = config.get('harnesses', HARNESSES)
    require(isinstance(harnesses, (list, tuple)) and all(harness in HARNESSES for harness in harnesses)
            and len(set(harnesses)) == len(harnesses), 'The pool needs distinct supported Harnesses.')
    pool = set()
    for model in config['pool']:
        require(isinstance(model, dict) and model.get('harness') in harnesses
                and 'model' in model and model_id(model['model']),
                'Each pool entry needs a supported Harness and a model ID.')
        require(model.get('family') is None or line(model['family']), 'Model family must be a single line.')
        pair = (model['harness'], model['model'])
        require(pair not in pool, 'Duplicate Harness and model in the pool.')
        pool.add(pair)
    for rule in config['rules']:
        require(isinstance(rule, dict) and line(rule.get('name')) and isinstance(rule.get('description'), str)
                and all(line(part) for part in rule['description'].splitlines() if part.strip())
                and bool(rule['description'].strip())
                and isinstance(rule.get('candidates'), list), 'Each rule needs a name and task description.')
        for candidate in rule['candidates']:
            require(isinstance(candidate, dict) and line(candidate.get('harness'))
                    and 'model' in candidate and model_id(candidate['model'])
                    and (candidate['harness'], candidate['model']) in pool and candidate.get('effort') in EFFORTS
                    and candidate.get('role', 'both') in ROLES,
                    'Each candidate needs a pool model, supported effort, and eligible role.')
    notes = config.get('launch_notes', {})
    require(isinstance(notes, dict) and isinstance(notes.get('project', ''), str)
            and isinstance(notes.get('harnesses', {}), dict), 'Invalid launch notes.')
    require(all(harness in HARNESSES and isinstance(note, str)
                for harness, note in notes.get('harnesses', {}).items()), 'Invalid per-Harness launch notes.')
    require(type(config.get('prefer_independent_reviewer', True)) is bool, 'Invalid Reviewer preference.')
    return config


def inline(value):
    longest = max((len(run) for run in re.findall(r'`+', value)), default=0)
    fence = '`' * (longest + 1)
    return f'{fence} {value} {fence}'


def show_model(model):
    return 'Harness default' if model is None else inline(model)


def effective_family(entry):
    return entry.get('family') or detected_family(entry['model'])


def markdown(config, newline):
    lines = [HEADING, '', '### Harness Pool', '']
    harnesses = config.get('harnesses', dict.fromkeys(model['harness'] for model in config['pool']))
    for harness in harnesses:
        lines.append(f'- {inline(harness)}')
        models = [model for model in config['pool'] if model['harness'] == harness]
        for entry in models:
            family = effective_family(entry)
            suffix = f' · family {inline(family)}' if family else ''
            lines.append(f"  - {show_model(entry['model'])}{suffix}")
        if not models:
            lines.append('  - No models configured.')
    if not harnesses:
        lines.append('No Harnesses configured.')
    lines.extend(['', '### Routing Rules', ''])
    for index, rule in enumerate(config['rules'], 1):
        description = ' '.join(part.strip() for part in rule['description'].splitlines() if part.strip())
        lines.append(f"{index}. {inline(rule['name'])} · {inline(description)}")
        lines.extend(f"   - {inline(row['harness'])} · {show_model(row['model'])} · effort {row['effort']}"
                     f" · {row.get('role', 'both')}"
                     for row in rule['candidates'])
        if not rule['candidates']:
            lines.append('   - No eligible candidates configured.')
    preference = 'enabled' if config.get('prefer_independent_reviewer', True) else 'disabled'
    lines.extend(['', '### Reviewer Preference', '', f'Preference for a different Harness and model family is {preference}.'])
    notes = config.get('launch_notes', {})
    launch_notes = [('Project-wide', notes.get('project', '')), *notes.get('harnesses', {}).items()]
    if any(note.strip() for _, note in launch_notes):
        lines.extend(['', '### Launch Notes'])
        for label, note in launch_notes:
            if note.strip():
                lines.extend(['', f'#### {label}', ''])
                lines.extend(f'> {part}' if part else '>' for part in note.strip('\r\n').splitlines())
    return newline.join(lines).rstrip() + newline


def reviewer_rank(candidate, family, worker, worker_family):
    if worker is None:
        return 0
    different_harness = candidate['harness'] != worker['harness']
    if family and worker_family:
        if family.strip().casefold() != worker_family.strip().casefold():
            return 0 if different_harness else 1
    elif different_harness:
        return 2
    return 3


def select(config, matches, role, runtime):
    if config is None:
        return {'status': 'legacy'}
    if not matches:
        return {'status': 'queued', 'reason': 'No routing rule matches the task.'}
    require(all(1 <= index <= len(config['rules']) for index in matches), 'Invalid routing rule position.')
    position = min(matches)
    rule = config['rules'][position - 1]
    decision = {'rule': rule['name'], 'position': position}
    eligible = [row for row in rule['candidates'] if row.get('role', 'both') in ('both', role)]
    if not eligible:
        return {**decision, 'status': 'queued', 'reason': f"Rule {rule['name']!r} has no {role}-eligible candidate."}
    runtime = Runtime(runtime)
    eligible, reason = runtime.candidates(eligible)
    if not eligible:
        return {**decision, 'status': 'queued', 'reason': f"Rule {rule['name']!r}: {reason}."}
    families = {pair(entry): effective_family(entry) for entry in config['pool']}
    worker = runtime.worker if role == 'reviewer' and config.get('prefer_independent_reviewer', True) else None
    worker_family = worker and (worker.get('family') or families.get(pair(worker)) or detected_family(worker['model']))

    def priority(candidate):
        return (reviewer_rank(candidate, families[pair(candidate)], worker, worker_family), *runtime.load(candidate))

    candidate = min(eligible, key=priority)
    assignment = {**candidate, 'family': families[pair(candidate)]}
    return {**decision, 'status': 'selected', 'assignment': assignment}


def policy_section(text):
    """Return the offsets of the routing section, skipping headings in fenced examples."""
    start = end = None
    fence = ''
    offset = 0
    for row in text.splitlines(keepends=True):
        content = row.rstrip('\r\n')
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})(.*)$', content)
        if marker:
            run, suffix = marker.groups()
            if not fence:
                fence = run
            elif run.startswith(fence) and not suffix.strip():
                fence = ''
        elif not fence and re.match(r'^ {0,3}#{1,2}(?:[ \t]|$)', content):
            title = re.sub(r'[ \t]+#+[ \t]*$', '', content).strip()
            if start is not None:
                end = offset
                break
            if title == HEADING:
                start = offset
        offset += len(row)
    return start, end if end is not None else len(text)


def read_bytes(path):
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return None


def decode_config(data):
    return None if data is None else validate(json.loads(data))


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        if path.exists():
            temporary.chmod(path.stat().st_mode)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def repository_lock(path):
    with path.open('a+b') as lock:
        lock.seek(0)
        if os.name == 'nt':
            import msvcrt

            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield


class Project:
    def __init__(self, root, policy, git_dir):
        self.root = root
        self.config = (root / CONFIG).resolve()
        self.policy = (root / policy).resolve()
        self.lock = threading.Lock()
        self.lock_path = git_dir / 'implement-tasks-routing.lock'
        require(self.config.is_relative_to(root) and self.policy.is_relative_to(root)
                and self.config != self.policy, 'Choose a policy file inside the project.')

    def snapshot(self):
        config = read_bytes(self.config)
        policy = read_bytes(self.policy)
        revision = hashlib.sha256(repr((config, policy)).encode()).hexdigest()
        return config, policy, revision

    def state(self):
        with self.lock, repository_lock(self.lock_path):
            config, policy, revision = self.snapshot()
        handwritten = ''
        if config is None and policy:
            text = policy.decode('utf-8-sig')
            start, end = policy_section(text)
            if start is not None:
                handwritten = text[start:end]
        config = decode_config(config) or default_config()
        families = {entry['model']: detected_family(entry['model']) for entry in config['pool'] if entry['model']}
        return {'project': self.root.name, 'config': config, 'families': families,
                'revision': revision, 'harnesses': HARNESSES, 'efforts': EFFORTS,
                'handwritten': handwritten}

    def render(self, config, policy):
        has_bom = bool(policy and policy.startswith(b'\xef\xbb\xbf'))
        text = policy.decode('utf-8-sig') if policy else ''
        first_break = re.search(r'\r\n|\n', text)
        newline = first_break[0] if first_break else '\n'
        start, end = policy_section(text)
        preview = markdown(config, newline)
        if start is None:
            if not text:
                text = '# Implement Tasks' + newline * 2
            elif not text.endswith(newline * 2):
                text += newline if text.endswith(newline) else newline * 2
            updated = text + preview
        else:
            section = text[start:end]
            separator = re.search(r'(?:[\t ]*\r?\n)+\Z', section)
            trailing = separator[0].split('\n', 1)[1] if separator else ''
            updated = text[:start] + preview + trailing + text[end:]
        return preview, updated.encode('utf-8-sig' if has_bom else 'utf-8')

    def edit(self, payload, save):
        require(isinstance(payload, dict), 'Expected a routing form.')
        config = validate(payload.get('config'))
        with self.lock, repository_lock(self.lock_path):
            _, old_policy, revision = self.snapshot()
            require(payload.get('revision') == revision, 'Project files changed. Reload the editor before saving.')
            preview, updated = self.render(config, old_policy)
            if save:
                encoded = (json.dumps(config, indent=2, ensure_ascii=False) + '\n').encode()
                atomic_write(self.policy, updated)
                try:
                    atomic_write(self.config, encoded)
                except OSError:
                    if old_policy is None:
                        self.policy.unlink()
                    else:
                        atomic_write(self.policy, old_policy)
                    raise
                _, _, revision = self.snapshot()
        return {'markdown': preview, 'revision': revision}


def serve(project, open_browser):
    prefix = '/' + secrets.token_urlsafe(24) + '/'

    class Editor(BaseHTTPRequestHandler):
        def authorized(self):
            return self.headers.get('Host') == f'127.0.0.1:{self.server.server_port}' and self.path.startswith(prefix)

        def respond(self, body, content_type, status=200):
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()
            self.wfile.write(body)

        def respond_json(self, value, status=200):
            self.respond(json.dumps(value).encode(), 'application/json', status)

        def do_GET(self):
            if self.path == '/favicon.ico':
                self.respond(b'', 'image/x-icon', 204)
                return
            if not self.authorized():
                self.send_error(404)
                return
            route = self.path[len(prefix):]
            if route == 'state':
                try:
                    self.respond_json(project.state())
                except (OSError, ValueError) as error:
                    self.respond_json({'error': str(error)}, 400)
                return
            if route.startswith('catalog/'):
                harness = route.removeprefix('catalog/')
                try:
                    require(harness in HARNESSES, 'Unknown Harness.')
                    ids = model_ids(harness, project.root)
                    self.respond_json({'models': ids, 'families': {model: detected_family(model) for model in ids}})
                except ValueError as error:
                    self.respond_json({'error': str(error)}, 400)
                return
            files = {'': ('index.html', 'text/html'), 'style.css': ('style.css', 'text/css'),
                     'editor.js': ('editor.js', 'text/javascript')}
            if route not in files:
                self.send_error(404)
                return
            filename, content_type = files[route]
            self.respond((ASSETS / filename).read_bytes(), content_type + '; charset=utf-8')

        def do_POST(self):
            route = self.path[len(prefix):]
            if not self.authorized() or route not in ('preview', 'save', 'family'):
                self.send_error(404)
                return
            try:
                require(self.headers.get_content_type() == 'application/json', 'Expected JSON.')
                length = int(self.headers.get('Content-Length', '0'))
                require(0 < length <= 1024 * 1024, 'Invalid form size.')
                payload = json.loads(self.rfile.read(length))
                if route == 'family':
                    require(isinstance(payload, dict) and 'model' in payload and model_id(payload['model']),
                            'Expected a model ID.')
                    self.respond_json({'family': detected_family(payload['model'])})
                else:
                    self.respond_json(project.edit(payload, save=route == 'save'))
            except (OSError, ValueError) as error:
                self.respond_json({'error': str(error)}, 400)

        def log_message(self, *_):
            pass

    with ThreadingHTTPServer(('127.0.0.1', 0), Editor) as server:
        url = f'http://127.0.0.1:{server.server_port}{prefix}'
        print(url, flush=True)
        if open_browser:
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--policy', type=Path, default=POLICY, help='Project-relative Markdown policy path.')
    commands = parser.add_subparsers(dest='command', required=True)
    editor = commands.add_parser('edit', help='Open the local routing editor.')
    editor.add_argument('--no-browser', action='store_true', help='Print the editor URL for manual opening.')
    commands.add_parser('rules', help='Print settings as JSON, or null for legacy routing.')
    selector = commands.add_parser('select', help='Select a candidate from the first rule matching the task.')
    selector.add_argument('--matches', type=int, nargs='*', default=[], help='Matching rules by 1-based position.')
    selector.add_argument('--role', choices=ROLES[1:], required=True)
    selector.add_argument('--runtime', action='store_true', help='Read invocation restrictions and usage as JSON from stdin.')
    arguments = parser.parse_args()
    try:
        result = subprocess.run(['git', 'rev-parse', '--show-toplevel', '--absolute-git-dir'], capture_output=True, check=True)
        root, git_dir = (Path(part).resolve() for part in os.fsdecode(result.stdout).splitlines())
        project = Project(root, arguments.policy, git_dir)
        if arguments.command == 'edit':
            serve(project, not arguments.no_browser)
        else:
            config = decode_config(read_bytes(project.config))
            result = config
            if arguments.command == 'select':
                runtime = json.load(sys.stdin) if arguments.runtime else {}
                result = select(config, arguments.matches, arguments.role, runtime)
            print(json.dumps(result))
    except subprocess.CalledProcessError:
        parser.exit(2, 'Run the routing command from a Git project.\n')
    except (OSError, ValueError) as error:
        parser.exit(2, f'{error}\n')


if __name__ == '__main__':
    main()
