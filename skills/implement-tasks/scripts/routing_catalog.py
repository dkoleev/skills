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
}

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


def model_ids(harness, root):
    if harness == 'claude':
        return ['haiku', 'sonnet', 'opus']
    if harness not in COMMANDS:
        return []
    binary = shutil.which(harness)
    if not binary:
        raise ValueError(f'{harness} is unavailable on PATH.')
    try:
        result = subprocess.run([binary, *COMMANDS[harness]], cwd=root, capture_output=True,
                                encoding='utf-8', errors='replace', check=True, timeout=15)
        if harness == 'codex':
            ids = [model['slug'] for model in json.loads(result.stdout)['models']]
        elif harness == 'kimi':
            ids = list(json.loads(result.stdout)['models'])
        elif harness == 'agy':
            ids = [row.split('\t', 1)[0] for row in result.stdout.splitlines() if '\t' in row]
        else:
            ids = [row for row in result.stdout.splitlines() if re.fullmatch(r'[^/\s]+/\S+', row)]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as error:
        raise ValueError(f'Could not read the {harness} model catalog.') from error
    return list(dict.fromkeys(model for model in ids if isinstance(model, str) and model.strip()))
