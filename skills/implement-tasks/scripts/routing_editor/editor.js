const editor = document.querySelector('#editor');
const previewButton = document.querySelector('#preview-button');
const saveButton = document.querySelector('#save-button');
const status = document.querySelector('#status');
const preview = document.querySelector('#preview');
const rules = document.querySelector('#rules');
const addRule = document.querySelector('#add-rule');
const pool = document.querySelector('#pool');
const availableHarness = document.querySelector('#available-harness');
const addHarness = document.querySelector('#add-harness');
const harnessTemplate = document.querySelector('#harness-template');
const removeDialog = document.querySelector('#remove-dialog');
const projectNotes = document.querySelector('#project-notes');
const harnessNotes = document.querySelector('#harness-notes');
const preferReviewer = document.querySelector('#prefer-reviewer');
const migration = document.querySelector('#migration');
const ruleTemplate = document.querySelector('#rule-template');
const candidateTemplate = document.querySelector('#candidate-template');
const catalogs = new Map();
const families = new Map();
let state;

async function request(route, payload) {
  const options = payload && {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  };
  const response = await fetch(route, options);
  const data = await response.json();
  if (!response.ok) throw new Error(data.error);
  return data;
}

function showStatus(message, error = false) {
  status.textContent = message;
  status.dataset.error = String(error);
}

function options(select, items) {
  select.replaceChildren(...items.map(item => new Option(item, item)));
}

function onAction(element, action, handler) {
  const button = element.querySelector(`[data-action="${action}"]`);
  button.addEventListener('click', handler);
  return button;
}

function connectField(element, object, property) {
  const input = element.querySelector(`[name="${property}"]`);
  input.value = object[property];
  input.addEventListener('input', () => { object[property] = input.value; });
  return input;
}

function modelLabel(model) {
  return model ?? 'Harness default';
}

function modelFamily(entry) {
  return entry.family || families.get(entry.model);
}

function confirmRemoval(title, description, includes, remove) {
  document.querySelector('#remove-title').textContent = title;
  const affected = state.config.rules.filter(rule => rule.candidates.some(includes));
  document.querySelector('#remove-description').textContent = affected.length
    ? `${description} These rules will be affected.` : description;
  document.querySelector('#affected-rules').replaceChildren(...affected.map(rule => {
    const item = document.createElement('li');
    const empty = rule.candidates.every(includes);
    item.textContent = `${rule.name || 'Unnamed rule'}${empty ? ' (will need a candidate)' : ''}`;
    return item;
  }));
  removeDialog.returnValue = '';
  removeDialog.addEventListener('close', () => {
    if (removeDialog.returnValue !== 'remove') return;
    for (const rule of affected) rule.candidates = rule.candidates.filter(candidate => !includes(candidate));
    state.config.pool = state.config.pool.filter(model => !includes(model));
    remove?.();
    renderPool();
    renderRules();
    renderNotes();
  }, {once: true});
  removeDialog.showModal();
}

function renderNotes() {
  const notes = state.config.launch_notes;
  projectNotes.value = notes.project;
  const harnesses = new Set([...state.config.harnesses, ...Object.keys(notes.harnesses)]);
  harnessNotes.replaceChildren(...[...harnesses].map(harness => {
    const label = document.createElement('label');
    label.textContent = `${harness} launch notes`;
    const input = document.createElement('textarea');
    input.rows = 3;
    input.value = notes.harnesses[harness] ?? '';
    input.addEventListener('input', () => {
      if (input.value) notes.harnesses[harness] = input.value;
      else delete notes.harnesses[harness];
    });
    label.append(input);
    return label;
  }));
}

function fillCatalog(list, harness) {
  options(list, catalogs.get(harness) ?? []);
}

function renderPool() {
  const choices = state.harnesses.filter(harness => !state.config.harnesses.includes(harness));
  options(availableHarness, choices);
  addHarness.disabled = !choices.length;
  pool.replaceChildren(...state.config.harnesses.map(harness => {
    const panel = harnessTemplate.content.firstElementChild.cloneNode(true);
    panel.querySelector('.harness-title').textContent = harness;
    const models = state.config.pool.filter(entry => entry.harness === harness);
    const list = panel.querySelector('datalist');
    const input = panel.querySelector('.new-model');
    const message = panel.querySelector('.catalog-status');
    list.id = `catalog-${harness}`;
    input.setAttribute('list', list.id);
    fillCatalog(list, harness);
    const add = async model => {
      if (model === '' || models.some(entry => entry.model === model)) {
        message.textContent = model === '' ? 'Enter a model ID.' : 'This model is already in the pool.';
        return;
      }
      state.config.pool.push({harness, model});
      renderPool();
      renderRules();
      if (model && !families.has(model)) {
        try {
          const {family} = await request('family', {model});
          families.set(model, family);
          for (const field of pool.querySelectorAll('input[data-model]')) {
            if (field.dataset.model === model) field.placeholder = family || 'Unknown';
          }
          renderRules();
        } catch (error) {
          showStatus(error.message, true);
        }
      }
    };
    onAction(panel, 'add-model', () => add(input.value.trim() ? input.value : ''));
    onAction(panel, 'add-default', () => add(null)).disabled = models.some(entry => entry.model === null);
    input.addEventListener('keydown', event => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      add(input.value.trim() ? input.value : '');
    });
    onAction(panel, 'remove-harness', () => confirmRemoval(`Remove ${harness}?`,
      'Candidate rows for this Harness will be removed from these rules.', entry => entry.harness === harness,
      () => { state.config.harnesses = state.config.harnesses.filter(item => item !== harness); }));
    const refresh = onAction(panel, 'catalog', async () => {
      refresh.disabled = true;
      message.textContent = 'Loading model catalog…';
      try {
        const {models: ids, families: known} = await request(`catalog/${harness}`);
        catalogs.set(harness, ids);
        for (const [id, family] of Object.entries(known)) families.set(id, family);
        fillCatalog(list, harness);
        message.textContent = ids.length ? `${ids.length} models available in the Model ID list.`
          : 'Enter an exact model ID or use the Harness default.';
      } catch (error) {
        message.textContent = error.message;
      } finally {
        refresh.disabled = false;
      }
    });
    panel.querySelector('.models').replaceChildren(...models.map(entry => {
      const item = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = modelLabel(entry.model);
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = 'Remove model';
      remove.setAttribute('aria-label', `Remove ${label.textContent}`);
      remove.addEventListener('click', () => confirmRemoval(`Remove ${label.textContent}?`,
        'Candidate rows for this model will be removed from these rules.',
        candidate => candidate.harness === harness && candidate.model === entry.model));
      const familyLabel = document.createElement('label');
      familyLabel.textContent = 'Model family';
      const family = document.createElement('input');
      family.value = entry.family ?? '';
      family.placeholder = families.get(entry.model) || 'Unknown';
      family.dataset.model = entry.model ?? '';
      family.addEventListener('input', () => {
        if (family.value.trim()) entry.family = family.value.trim();
        else delete entry.family;
      });
      family.addEventListener('change', () => renderRules());
      familyLabel.append(family);
      item.append(label, remove, familyLabel);
      return item;
    }));
    return panel;
  }));
}

function renderRules(focus) {
  rules.replaceChildren(...state.config.rules.map((rule, position) => {
    const panel = ruleTemplate.content.firstElementChild.cloneNode(true);
    const title = panel.querySelector('.rule-title');
    title.textContent = rule.name || 'New rule';
    const name = connectField(panel, rule, 'name');
    name.addEventListener('input', () => { title.textContent = name.value || 'New rule'; });
    connectField(panel, rule, 'description');
    const move = offset => {
      const target = position + offset;
      const items = state.config.rules;
      [items[position], items[target]] = [items[target], items[position]];
      renderRules(rule);
    };
    onAction(panel, 'up', () => move(-1)).disabled = position === 0;
    onAction(panel, 'down', () => move(1)).disabled = position === state.config.rules.length - 1;
    onAction(panel, 'remove', () => {
      state.config.rules.splice(position, 1);
      renderRules();
    });
    onAction(panel, 'add-candidate', () => {
      const {harness, model} = state.config.pool[0];
      rule.candidates.push({harness, model, effort: 'default', role: 'both'});
      renderRules(rule.candidates.at(-1));
    }).disabled = !state.config.pool.length;
    panel.querySelector('.empty-rule').hidden = rule.candidates.length !== 0;
    panel.querySelector('.candidates').replaceChildren(...rule.candidates.map((candidate, index) => {
      const row = candidateTemplate.content.firstElementChild.cloneNode(true);
      const model = row.querySelector('[name="model"]');
      state.config.pool.forEach((entry, index) => {
        const selected = entry.harness === candidate.harness && entry.model === candidate.model;
        const family = modelFamily(entry);
        const label = `${entry.harness} · ${modelLabel(entry.model)}${family ? ` · ${family}` : ''}`;
        model.add(new Option(label, index, selected, selected));
      });
      model.addEventListener('input', () => {
        const entry = state.config.pool[model.value];
        candidate.harness = entry.harness;
        candidate.model = entry.model;
      });
      options(row.querySelector('[name="effort"]'), state.efforts);
      candidate.role ??= 'both';
      for (const field of ['effort', 'role']) connectField(row, candidate, field);
      onAction(row, 'remove-candidate', () => {
        rule.candidates.splice(index, 1);
        renderRules(rule);
      });
      if (candidate === focus) row.querySelector('[name="model"]').setAttribute('data-focus', '');
      return row;
    }));
    if (rule === focus) name.setAttribute('data-focus', '');
    return panel;
  }));
  rules.querySelector('[data-focus]')?.focus();
}

async function update(route) {
  if (!editor.reportValidity()) return;
  previewButton.disabled = saveButton.disabled = editor.inert = true;
  try {
    const data = await request(route, {config: state.config, revision: state.revision});
    preview.textContent = data.markdown;
    state.revision = data.revision;
    if (route === 'save') migration.hidden = true;
    showStatus(route === 'save' ? 'Routing saved.' : 'Preview updated.');
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    previewButton.disabled = saveButton.disabled = editor.inert = false;
  }
}

previewButton.addEventListener('click', () => update('preview'));
addHarness.addEventListener('click', () => {
  state.config.harnesses.push(availableHarness.value);
  renderPool();
  renderNotes();
  pool.lastElementChild.querySelector('input').focus();
});
projectNotes.addEventListener('input', () => { state.config.launch_notes.project = projectNotes.value; });
preferReviewer.addEventListener('change', () => { state.config.prefer_independent_reviewer = preferReviewer.checked; });
addRule.addEventListener('click', () => {
  const rule = {name: '', description: '', candidates: []};
  state.config.rules.push(rule);
  renderRules(rule);
});
editor.addEventListener('submit', event => {
  event.preventDefault();
  update('save');
});

async function load() {
  try {
    state = await request('state');
    document.querySelector('#project').textContent = state.project;
    state.config.harnesses ??= [...new Set(state.config.pool.map(entry => entry.harness))];
    for (const [id, family] of Object.entries(state.families)) families.set(id, family);
    preferReviewer.checked = state.config.prefer_independent_reviewer ?? true;
    state.config.launch_notes ??= {project: '', harnesses: {}};
    state.config.launch_notes.project ??= '';
    state.config.launch_notes.harnesses ??= {};
    document.querySelector('#handwritten').textContent = state.handwritten;
    migration.hidden = !state.handwritten;
    renderPool();
    renderRules();
    renderNotes();
    const data = await request('preview', {config: state.config, revision: state.revision});
    preview.textContent = data.markdown;
    previewButton.disabled = saveButton.disabled = addRule.disabled = false;
  } catch (error) {
    showStatus(error.message, true);
  }
}

load();
