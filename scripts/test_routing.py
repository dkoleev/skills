"""Exercise the routing editor and Runner commands in disposable Git projects."""

import json
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.dont_write_bytecode = True


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

    def test_background_editor_outlives_launcher_and_can_be_closed(self):
        launcher = self.command('open', '--no-browser', check=True, timeout=10)
        self.url = launcher.stdout.strip()
        self.assertTrue(self.url.startswith('http://127.0.0.1:'))
        try:
            state = self.request('state')
            self.assertTrue(state['background'])
            self.assertEqual(state['project'], self.repo.name)
            settings = self.policy.with_name('implement-tasks-routing.json')
            settings.write_text('{', encoding='utf-8')
            with self.assertRaises(HTTPError) as rejected:
                self.request('state')
            self.assertTrue(json.load(rejected.exception)['background'])
        finally:
            self.assertEqual(self.request('close', {}), {'closed': True})
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            try:
                self.request('state')
            except (URLError, ConnectionError, TimeoutError):
                break
            time.sleep(0.05)
        else:
            self.fail('Background editor kept listening after close.')
        self.assertFalse(self.policy.exists())

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

    def test_editor_rejects_padded_ids_unsupported_efforts_and_duplicates(self):
        self.start_editor()
        form = self.request('state')
        self.assertEqual(form['policy'], POLICY)
        self.assertIn('xhigh', form['efforts']['codex'])
        self.assertEqual(form['efforts']['opencode'], ['default'])
        codex = {'harness': 'codex', 'model': 'gpt-test'}
        config = form['config']
        config['harnesses'] = ['codex', 'agy', 'opencode']
        rule = config['rules'][0]

        def rejected(message):
            with self.assertRaises(HTTPError) as error:
                self.request('preview', form)
            self.assertEqual(error.exception.code, 400)
            self.assertIn(message, json.load(error.exception)['error'])

        config['pool'] = [{'harness': 'codex', 'model': ' gpt-test '}]
        rejected('model ID')
        opus = {'harness': 'agy', 'model': 'claude-opus-test', 'efforts': ['low', 'medium', 'high']}
        variant = {'harness': 'agy', 'model': 'gemini-test-high'}
        opencode = {'harness': 'opencode', 'model': None}
        pick = lambda entry, effort: {'harness': entry['harness'], 'model': entry['model'], 'effort': effort}
        config['pool'] = [codex, opus, variant, opencode]
        for entry, effort in ((opus, 'xhigh'), (variant, 'high'), (opencode, 'low')):
            rule['candidates'] = [pick(entry, effort)]
            rejected(f'does not support {effort}')
        config['pool'][1]['efforts'] = ['low', 'low']
        rejected('Model efforts')
        config['pool'][1]['efforts'] = ['low', 'medium', 'high']
        rule['candidates'] = [pick(opus, 'high'), pick(variant, 'default'), pick(codex, 'xhigh')]
        self.assertIn('efforts low, medium, high', self.request('preview', form)['markdown'])
        rule['candidates'] = [{**codex, 'effort': 'high'}, {**codex, 'effort': 'high', 'role': 'both'}]
        rejected('same candidate twice')
        rule['candidates'][1]['role'] = 'reviewer'
        self.request('save', form)
        with self.assertRaises(HTTPError) as stale:
            self.request('save', form)
        self.assertEqual(stale.exception.code, 409)

    def test_tie_breaks_escalation_and_editor_warnings(self):
        self.start_editor()
        form = self.request('state')
        config = form['config']
        self.assertTrue(all('sample description' in text for text in self.request('preview', form)['warnings']))
        self.assertEqual(self.request('catalog/claude')['efforts']['opus'], ['low', 'medium', 'high', 'xhigh', 'max'])
        codex = {'harness': 'codex', 'model': 'gpt-test'}
        claude = {'harness': 'claude', 'model': 'opus'}
        config['harnesses'] = ['codex', 'claude']
        config['pool'] = [codex, claude]
        for rule in config['rules']:
            rule['description'] = f"Project tasks for {rule['name']}."
        rule = config['rules'][0]
        rule['candidates'] = [{**codex, 'effort': 'low', 'escalate_to': 'xhigh'}, {**claude, 'effort': 'high'}]
        saved = self.request('save', form)
        form['revision'] = saved['revision']
        self.assertIn('effort low · escalate to xhigh · both', saved['markdown'])
        self.assertEqual(saved['warnings'], [])
        self.assertEqual(self.selection('worker', 1)['assignment']['escalate_to'], 'xhigh')
        quota = {'models': [{**codex, 'quota_remaining': 3}, {**claude, 'quota_remaining': 9}]}
        self.assertEqual(self.selection('worker', 1, runtime=quota)['assignment']['harness'], 'claude')
        rotation = {'models': [{**codex, 'assigned': 2}, {**claude, 'assigned': 1}]}
        self.assertEqual(self.selection('worker', 1, runtime=rotation)['assignment']['harness'], 'claude')
        rotation['models'][1]['active'] = 1
        self.assertEqual(self.selection('worker', 1, runtime=rotation)['assignment']['harness'], 'codex')

        def rejected(message):
            with self.assertRaises(HTTPError) as error:
                self.request('preview', form)
            self.assertIn(message, json.load(error.exception)['error'])

        rule['candidates'][0]['escalate_to'] = 'low'
        rejected('cannot escalate')
        rule['candidates'][0].update(escalate_to='xhigh', role='reviewer')
        rejected('Workers only')
        rule['candidates'] = [{**codex, 'effort': 'low', 'role': 'worker'}, {**codex, 'effort': 'high'}]
        config['launch_notes'] = {'project': '', 'harnesses': {'claude': 'Set ANTHROPIC_BASE_URL to the z.ai endpoint.'}}
        found = self.request('preview', form)['warnings']
        self.assertTrue(any('never selected as worker because' in text for text in found))
        self.assertTrue(any('custom endpoint' in text and 'opus' in text for text in found))
        config['pool'][1]['family'] = 'GLM'
        self.assertFalse(any('custom endpoint' in text for text in self.request('preview', form)['warnings']))
        self.assertFalse((ROUTING.parent / '__pycache__').exists())

    def test_agy_catalog_merges_effort_variants(self):
        sys.path.insert(0, str(ROUTING.parent))
        from routing_catalog import merge_variants
        rows = ['Fetching available models...', 'gemini-x-high	Gemini X (High)', 'gemini-x-low	Gemini X (Low)',
                'orchestrator	Orchestrator (Carbon)', 'oss-medium	OSS (Medium)', 'odd-name	Odd (High)']
        self.assertEqual(merge_variants(rows), {'gemini-x': ['high', 'low'], 'orchestrator': None,
                                                'oss': ['medium'], 'odd-name': None})

    def test_pool_supports_catalog_custom_and_default_models(self):
        self.start_editor()
        form = self.request('state')
        discovered = self.request('catalog/claude')['models'][0]
        manual = {'harness': 'claude', 'model': 'custom/Exact-ID'}
        default = {'harness': 'crush', 'model': None}
        self.assertIn('crush', form['harnesses'])
        form['config']['harnesses'] = ['claude', 'crush']
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
        assignment = self.selection('worker', 1)['assignment']
        self.assertEqual(assignment['harness'], 'crush')
        self.assertIsNone(assignment['model'])
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
        self.assertIn('family `Claude`', saved['markdown'])
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
