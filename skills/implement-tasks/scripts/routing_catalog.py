"""Discover selectable model IDs through the installed Harness CLIs."""

import json
import re
import shutil
import subprocess


COMMANDS = {
    'codex': ('debug', 'models'),
    'agy': ('models',),
    'kimi': ('provider', 'list', '--json'),
    'opencode': ('models',),
    'crush': ('models',),
}

EFFORTS = ('default', 'low', 'medium', 'high', 'xhigh', 'max', 'ultra')
EFFORT_NAME = re.compile(r'\((low|medium|high|xhigh|max|ultra)\)$', re.IGNORECASE)

FAMILIES = {
    'GPT': r'(?:gpt[-.]|o[1-9](?:$|[-.]))',
    'Claude': r'(?:claude[-.]|haiku$|sonnet$|opus$)',
    'Gemini': r'gemini[-.]',
    'Kimi': r'(?:kimi[-.]|k[0-9](?:$|[-.]))',
    'GLM': r'glm[-.]',
    'DeepSeek': r'deepseek[-.]',
    'Qwen': r'qwen(?:$|[-.0-9])',
    'Grok': r'grok[-.]',
    'Llama': r'llama(?:$|[-.0-9])',
    'MiniMax': r'minimax[-.]',
}


def detected_family(model):
    if model is None:
        return None
    short_id = model.rsplit('/', 1)[-1].casefold()
    return next((family for family, prefix in FAMILIES.items() if re.match(prefix, short_id)), None)


def merge_variants(rows):
    """Fold agy rows such as `gemini-x-high<TAB>Gemini X (High)` into base IDs with their efforts."""
    models = {}
    for row in rows:
        if '\t' not in row:
            continue
        model, name = (part.strip() for part in row.split('\t', 1))
        match = EFFORT_NAME.search(name)
        effort = match and match[1].lower()
        if effort and model.endswith(f'-{effort}'):
            base = model.removesuffix(f'-{effort}')
            models[base] = [*(models.get(base) or []), effort]
        else:
            models.setdefault(model, None)
    return models


def known_efforts(levels):
    efforts = sorted({level for level in levels if level in EFFORTS[1:]}, key=EFFORTS.index)
    return efforts or None


def catalog(harness, root):
    """Return {model ID: supported efforts, or None when the catalog does not say}."""
    if harness == 'claude':
        return dict.fromkeys(['haiku', 'sonnet', 'opus'])
    if harness not in COMMANDS:
        return {}
    binary = shutil.which(harness)
    if not binary:
        raise ValueError(f'{harness} is unavailable on PATH.')
    try:
        result = subprocess.run([binary, *COMMANDS[harness]], cwd=root, capture_output=True,
                                encoding='utf-8', errors='replace', check=True, timeout=15)
        if harness == 'codex':
            models = {model['slug']: known_efforts(level['effort'] for level in model.get('supported_reasoning_levels') or [])
                      for model in json.loads(result.stdout)['models']}
        elif harness == 'kimi':
            models = dict.fromkeys(json.loads(result.stdout)['models'])
        elif harness == 'agy':
            models = {model: efforts and known_efforts(efforts)
                      for model, efforts in merge_variants(result.stdout.splitlines()).items()}
        else:
            models = dict.fromkeys(row for row in result.stdout.splitlines() if re.fullmatch(r'[^/\s]+/\S+', row))
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f'Could not read the {harness} model catalog.') from error
    return {model: efforts for model, efforts in models.items() if isinstance(model, str) and model.strip()}
