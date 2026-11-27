"""Exercise the routing editor and Runner commands in disposable Git projects."""

import json
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


ROUTING = Path(__file__).resolve().parents[1] / 'skills/implement-tasks/scripts/routing.py'
POLICY = '.agents/implement-tasks-auto-merge.md'


class RoutingWorkflow(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.repo = Path(directory.name)
        subprocess.run(['git', 'init', '--quiet'], cwd=self.repo, check=True)
        self.policy = self.repo / POLICY
        self.policy.parent.mkdir()

    def command(self, *args, **options):
        return subprocess.run([sys.executable, str(ROUTING), *args], cwd=self.repo,
                              capture_output=True, text=True, encoding='utf-8', **options)

    def start_editor(self, *args):
        server = subprocess.Popen([sys.executable, str(ROUTING), *args, 'edit', '--no-browser'],
                                  cwd=self.repo, stdout=subprocess.PIPE, text=True)
        self.addCleanup(server.stdout.close)
        self.addCleanup(server.wait, 5)
        self.addCleanup(server.terminate)
        self.url = server.stdout.readline().strip()
        self.assertTrue(self.url.startswith('http://127.0.0.1:'))

    def request(self, route, payload=None, *, url=None):
        request = Request((url or self.url) + route)
        if payload is not None:
            request.add_header('Content-Type', 'application/json')
            request.data = json.dumps(payload).encode()
        with urlopen(request, timeout=5) as response:
            return json.load(response)

    def test_legacy_projects_report_missing_structured_configuration(self):
        self.assertIsNone(json.loads(self.command('rules', check=True).stdout))

    def test_two_editors_reject_a_stale_concurrent_save(self):
        self.start_editor()
        first_url = self.url
        self.start_editor()
        second_url = self.url
        first = self.request('state', url=first_url)
        second = self.request('state', url=second_url)
        first['config']['rules'][0]['name'] = 'First edit'
        second['config']['rules'][0]['name'] = 'Second edit'

        def submit(url, form):
            try:
                return self.request('save', form, url=url)['markdown']
            except HTTPError as error:
                self.assertIn('Project files changed', json.load(error)['error'])
                return None

        with ThreadPoolExecutor() as executor:
            saves = [executor.submit(submit, first_url, first), executor.submit(submit, second_url, second)]
            saved = [result for save in saves if (result := save.result()) is not None]
        self.assertEqual(len(saved), 1)
        self.assertIn(saved[0], self.policy.read_text(encoding='utf-8'))

    def test_editor_saves_exact_preview_and_preserves_adjacent_sections(self):
        before = '# Policy\r\n\r\n```md\r\n## Harness Pool & Routing\r\n```\r\n\r\n'
        old = '## Harness Pool & Routing\r\n\r\nHandwritten settings.\r\n'
        after = '\r\n## Delivery Mode\r\n\r\nlocal\r\n'
        self.policy.write_bytes(('\ufeff' + before + old + after).encode())
        self.start_editor()
        form = self.request('state')
        self.assertEqual(form['handwritten'], old + '\r\n')
        self.assertEqual(self.policy.read_bytes(), ('\ufeff' + before + old + after).encode())
        pair = {'harness': 'codex', 'model': 'custom/Model@2026-11'}
        form['config']['harnesses'] = ['codex']
        form['config']['pool'] = [pair]
        form['config']['rules'][0]['candidates'] = [{**pair, 'effort': 'medium'}]
        preview = self.request('preview', form)['markdown']
        self.assertIn('custom/Model@2026-11', preview)
        self.assertIsNone(json.loads(self.command('rules', check=True).stdout))
        self.assertEqual(self.request('save', form)['markdown'], preview)
        self.assertEqual(self.policy.read_bytes(), ('\ufeff' + before + preview + after).encode())
        self.assertEqual(self.request('state')['config'], form['config'])
        self.assertEqual(json.loads(self.command('rules', check=True).stdout), form['config'])

        with self.assertRaises(HTTPError) as rejected:
            self.request('save', form)
        self.assertIn('Project files changed', json.load(rejected.exception)['error'])

    def selection(self, role, *positions, **options):
        runtime = options.pop('runtime', None)
        flags = ['--runtime'] if runtime is not None else []
        return json.loads(self.command('select', '--role', role, *flags, '--matches',
                                       *map(str, positions), check=True,
                                       input=json.dumps(runtime) if flags else None, **options).stdout)

    def test_order_role_eligibility_and_queue_reasons(self):
        self.start_editor()
        form = self.request('state')
        first, second = form['config']['rules']
        self.assertEqual(first['name'], 'High-risk / architectural')
        self.assertEqual(second['name'], 'Typical / mechanical')
        codex = {'harness': 'codex', 'model': 'custom-a'}
        claude = {'harness': 'claude', 'model': 'custom-b'}
        form['config']['harnesses'] = ['codex', 'claude']
        form['config']['pool'] = [codex, claude]
        first['candidates'] = [{**claude, 'effort': 'high', 'role': 'reviewer'},
                               {**codex, 'effort': 'medium', 'role': 'worker'}]
        second['candidates'] = [{**codex, 'effort': 'low'}]
        form['revision'] = self.request('save', form)['revision']
        self.assertEqual(self.selection('worker', 2, 1)['assignment']['effort'], 'medium')
        self.assertEqual(self.selection('reviewer', 1, 2)['assignment']['harness'], 'claude')
        self.assertIn('No routing rule', self.selection('worker')['reason'])
        form['config']['rules'].reverse()
        form['revision'] = self.request('save', form)['revision']
        self.assertEqual(self.selection('worker', 1, 2)['assignment']['effort'], 'low')
        self.assertEqual(self.request('state')['config'], form['config'])
        form['config']['rules'].reverse()
        first['candidates'].pop()
        self.request('save', form)
        decision = self.selection('worker', 1, 2)
        self.assertEqual(decision['status'], 'queued')
        self.assertIn('no worker-eligible candidate', decision['reason'])

    def test_pool_supports_catalog_custom_and_default_models(self):
        self.start_editor()
        form = self.request('state')
        discovered = self.request('catalog/claude')['models'][0]
        manual = {'harness': 'claude', 'model': 'custom/Exact-ID'}
        default = {'harness': 'codex', 'model': None}
        form['config']['harnesses'] = ['claude', 'codex']
        form['config']['pool'] = [manual, {'harness': 'claude', 'model': discovered}, default]
        rule = form['config']['rules'][0]
        rule['candidates'] = [{**manual, 'effort': 'medium'}, {**default, 'effort': 'default'}]
        form['revision'] = self.request('save', form)['revision']
        self.assertNotIn(manual['model'], self.request('catalog/claude')['models'])
        self.assertEqual(self.request('state')['config'], form['config'])
        self.assertEqual(self.selection('worker', 1)['assignment']['model'], manual['model'])
        form['config']['pool'].remove(manual)
        with self.assertRaises(HTTPError):
            self.request('save', form)
        rule['candidates'].pop(0)
        form['revision'] = self.request('save', form)['revision']
        self.assertIsNone(self.selection('worker', 1)['assignment']['model'])
        self.assertIn('Harness default', self.policy.read_text(encoding='utf-8'))

    def test_migration_preserves_custom_policy_and_reopens_launch_notes(self):
        custom = self.repo / '.agents/other-policy.md'
        start = '# Project Policy\n\n'
        end = '\n## Approval rules\n\nLeave this alone.\n'
        handwritten = '## Harness Pool & Routing\n\nUse a custom Claude endpoint.\n'
        custom.write_bytes((start + handwritten + end).encode())
        self.start_editor('--policy', '.agents/other-policy.md')
        form = self.request('state')
        self.assertIn(handwritten, form['handwritten'])
        form['config']['launch_notes'] = {'project': 'Use PowerShell.\n\n## Shell',
                                          'harnesses': {'claude': 'Use the configured custom endpoint.'}}
        preview = self.request('preview', form)['markdown']
        self.assertIn('> ## Shell', preview)
        self.assertEqual(custom.read_bytes(), (start + handwritten + end).encode())
        self.assertFalse(self.policy.exists())
        self.request('save', form)
        self.assertEqual(custom.read_bytes(), (start + preview + end).encode())
        reopened = self.request('state')
        self.assertEqual(reopened['handwritten'], '')
        self.assertEqual(reopened['config']['launch_notes'], form['config']['launch_notes'])
        self.assertEqual(self.request('preview', reopened)['markdown'], preview)

    def test_live_capacity_and_one_run_filters_apply_within_the_first_rule(self):
        self.start_editor()
        form = self.request('state')
        codex = {'harness': 'codex', 'model': 'first'}
        claude = {'harness': 'claude', 'model': 'second'}
        fallback = {'harness': 'agy', 'model': 'lower-priority'}
        config = form['config']
        config['harnesses'] = ['codex', 'claude', 'agy']
        config['pool'] = [codex, claude, fallback]
        config['rules'][0]['candidates'] = [{**model, 'effort': 'medium'} for model in (codex, claude)]
        config['rules'][1]['candidates'] = [{**fallback, 'effort': 'low'}]
        self.request('save', form)
        before = self.command('rules', check=True).stdout
        first = self.selection('worker', 1, 2)['assignment']
        self.assertEqual(first['harness'], 'codex')
        busy = {'harnesses': {'codex': {'active': 1, 'capacity': 2}}}
        self.assertEqual(self.selection('worker', 1, 2, runtime=busy)['assignment']['harness'], 'claude')
        busy['allowed_harnesses'] = ['codex']
        self.assertEqual(self.selection('worker', 1, 2, runtime=busy)['assignment']['harness'], 'codex')
        busy['harnesses']['codex']['active'] = 2
        self.assertIn('at capacity', self.selection('worker', 1, 2, runtime=busy)['reason'])
        exhausted = {'models': [{**codex, 'quota_remaining': 0}]}
        self.assertEqual(self.selection('worker', 1, 2, runtime=exhausted)['assignment']['harness'], 'claude')
        exhausted['harnesses'] = {'claude': {'quota_remaining': 0}}
        self.assertIn('out of quota', self.selection('worker', 1, 2, runtime=exhausted)['reason'])
        restriction = {'allowed_harnesses': ['agy']}
        self.assertIn('invocation restriction', self.selection('worker', 1, 2, runtime=restriction)['reason'])
        self.assertEqual(self.selection('worker', 1, 2)['assignment'], first)
        self.assertEqual(self.command('rules', check=True).stdout, before)

    def test_reviewer_prefers_independence_within_runtime_eligibility(self):
        self.start_editor()
        form = self.request('state')
        worker = {'harness': 'codex', 'model': 'openai/gpt-test'}
        same_vendor = {'harness': 'codex', 'model': 'custom/alternate-family'}
        cross_vendor = {'harness': 'claude', 'model': 'custom/exact-id'}
        unknown = {'harness': 'agy', 'model': 'vendor/opaque-id'}
        reviewer = {'effort': 'high', 'role': 'reviewer'}
        config = form['config']
        config['harnesses'] = ['codex', 'claude', 'agy']
        config['pool'] = [worker, {**same_vendor, 'family': 'Gemini'}, {**cross_vendor, 'family': 'Claude'}, unknown]
        first, second = config['rules']
        first['candidates'] = [{**model, **reviewer} for model in (worker, unknown, same_vendor, cross_vendor)]
        second['candidates'] = [{**cross_vendor, **reviewer}]
        saved = self.request('save', form)
        form['revision'] = saved['revision']
        self.assertIn('family ` Claude `', saved['markdown'])
        self.assertEqual(self.request('family', {'model': worker['model']})['family'], 'GPT')
        self.assertEqual(self.request('state')['config'], config)
        runtime = {'worker': worker, 'harnesses': {'claude': {'active': 2}}}
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['model'], cross_vendor['model'])
        self.assertEqual(self.selection('reviewer', 2, runtime=runtime)['assignment']['family'], 'Claude')
        runtime['harnesses']['claude']['quota_remaining'] = 0
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['model'], same_vendor['model'])
        first['candidates'][2]['role'] = 'worker'
        form['revision'] = self.request('save', form)['revision']
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['model'], unknown['model'])
        runtime['allowed_harnesses'] = ['codex']
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['model'], worker['model'])
        runtime = {'worker': {'harness': 'codex', 'model': None}}
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['harness'], 'agy')
        config['prefer_independent_reviewer'] = False
        saved = self.request('save', form)
        self.assertIn('model family is disabled.', saved['markdown'])
        self.assertEqual(self.selection('reviewer', 1, runtime=runtime)['assignment']['model'], worker['model'])


if __name__ == '__main__':
    unittest.main()
