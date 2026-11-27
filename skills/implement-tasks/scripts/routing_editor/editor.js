const editor = document.querySelector('#editor');
const workspace = document.querySelector('#workspace');
const saveButton = document.querySelector('#save-button');
const unsaved = document.querySelector('#unsaved');
const status = document.querySelector('#status');
const preview = document.querySelector('#preview');
const stopEditor = document.querySelector('#stop-editor');
const rules = document.querySelector('#rules');
const addRule = document.querySelector('#add-rule');
const pool = document.querySelector('#pool');
const availableHarness = document.querySelector('#available-harness');
const addHarness = document.querySelector('#add-harness');
const harnessTemplate = document.querySelector('#harness-template');
const removeDialog = document.querySelector('#remove-dialog');
const confirmAction = document.querySelector('#confirm-action');
const projectNotes = document.querySelector('#project-notes');
const harnessNotes = document.querySelector('#harness-notes');
const preferReviewer = document.querySelector('#prefer-reviewer');
const migration = document.querySelector('#migration');
const ruleTemplate = document.querySelector('#rule-template');
const candidateTemplate = document.querySelector('#candidate-template');
const catalogs = new Map();
const catalogStatus = new Map();
const loadingCatalogs = new Set();
const families = new Map();
let state;
let savedConfig;
let previewTimer;
let previewRequest = 0;

async function request(route, payload) {
  const options = payload && {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(payload),
  };
  const response = await fetch(route, options);
  const data = await response.json();
  if (!response.ok) throw Object.assign(new Error(data.error), {data, status: response.status});
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

function familySummary(entry) {
  const detected = families.get(entry.model);
  if (entry.family) return `Family: ${entry.family}`;
  return detected ? `Family: ${detected} (detected)` : 'Family: unknown';
}

function swap(items, index, offset) {
  [items[index], items[index + offset]] = [items[index + offset], items[index]];
}

function dirty() {
  return JSON.stringify(state.config) !== savedConfig;
}

function changed() {
  if (savedConfig === undefined) return;
  unsaved.hidden = !dirty();
  preview.dataset.stale = '';
  clearTimeout(previewTimer);
  previewTimer = setTimeout(refreshPreview, 300);
}

function ask(title, description, items, action) {
  document.querySelector('#remove-title').textContent = title;
  document.querySelector('#remove-description').textContent = description;
  document.querySelector('#affected-rules').replaceChildren(...items.map(text => {
    const item = document.createElement('li');
    item.textContent = text;
    return item;
  }));
  confirmAction.textContent = action;
  removeDialog.returnValue = '';
  removeDialog.showModal();
  return new Promise(resolve => removeDialog.addEventListener('close',
    () => resolve(removeDialog.returnValue === 'remove'), {once: true}));
}

async function confirmRemoval(title, description, includes, remove) {
  const affected = state.config.rules.filter(rule => rule.candidates.some(includes));
  const items = affected.map(rule =>
    `${rule.name || 'Unnamed rule'}${rule.candidates.every(includes) ? ' (will need a candidate)' : ''}`);
  if (!await ask(title, affected.length ? `${description} These rules will be affected.` : description, items, 'Remove')) return;
  for (const rule of affected) rule.candidates = rule.candidates.filter(candidate => !includes(candidate));
  state.config.pool = state.config.pool.filter(model => !includes(model));
  remove?.();
  renderPool();
  renderRules();
  renderNotes();
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
  changed();
}

function harnessPanel(harness) {
  return [...pool.children].find(panel => panel.dataset.harness === harness);
}

function showCatalog(panel, harness) {
  options(panel.querySelector('datalist'), catalogs.get(harness) ?? []);
  panel.querySelector('.catalog-status').textContent = catalogStatus.get(harness) ?? '';
  panel.querySelector('[data-action="catalog"]').disabled = loadingCatalogs.has(harness);
}

async function loadCatalog(harness) {
  loadingCatalogs.add(harness);
  catalogStatus.set(harness, 'Loading models…');
  const sync = () => { const panel = harnessPanel(harness); if (panel) showCatalog(panel, harness); };
  sync();
  try {
    const {models: ids, families: known} = await request(`catalog/${harness}`);
    catalogs.set(harness, ids);
    for (const [id, family] of Object.entries(known)) families.set(id, family);
    catalogStatus.set(harness, ids.length ? `${ids.length} models available in the Model ID list.`
      : 'No model catalog for this Harness. Enter an exact model ID or use the Harness default.');
  } catch (error) {
    catalogStatus.set(harness, error.message);
  } finally {
    loadingCatalogs.delete(harness);
    sync();
  }
}

function renderPool(focus) {
  const choices = state.harnesses.filter(harness => !state.config.harnesses.includes(harness));
  options(availableHarness, choices);
  addHarness.disabled = !choices.length;
  pool.replaceChildren(...state.config.harnesses.map(harness => {
    const panel = harnessTemplate.content.firstElementChild.cloneNode(true);
    panel.dataset.harness = harness;
    panel.querySelector('.harness-title').textContent = harness;
    const models = state.config.pool.filter(entry => entry.harness === harness);
    const list = panel.querySelector('datalist');
    const input = panel.querySelector('.new-model');
    const message = panel.querySelector('.catalog-status');
    list.id = `catalog-${harness}`;
    input.setAttribute('list', list.id);
    input.addEventListener('focus', () => { if (!catalogStatus.has(harness)) loadCatalog(harness); });
    const add = async model => {
      if (model === '' || models.some(entry => entry.model === model)) {
        message.textContent = model === '' ? 'Enter a model ID.' : 'This model is already in the pool.';
        return;
      }
      state.config.pool.push({harness, model});
      renderPool(harness);
      renderRules();
      if (model && !families.has(model)) {
        try {
          const {family} = await request('family', {model});
          families.set(model, family);
          for (const summary of pool.querySelectorAll('summary[data-model]')) {
            if (summary.dataset.model === model) summary.textContent = familySummary({model});
          }
          for (const field of pool.querySelectorAll('input[data-model]')) {
            if (field.dataset.model === model) field.placeholder = family || 'Unknown';
          }
          renderRules();
        } catch (error) {
          showStatus(error.message, true);
        }
      }
    };
    onAction(panel, 'add-model', () => add(input.value.trim()));
    onAction(panel, 'add-default', () => add(null)).disabled = models.some(entry => entry.model === null);
    input.addEventListener('keydown', event => {
      if (event.key !== 'Enter') return;
      event.preventDefault();
      add(input.value.trim());
    });
    onAction(panel, 'remove-harness', () => {
      const notes = state.config.launch_notes.harnesses;
      const extra = notes[harness] ? ' Its launch notes will be removed too.' : '';
      confirmRemoval(`Remove ${harness}?`, `Candidate rows for this Harness will be removed.${extra}`,
        entry => entry.harness === harness, () => {
          state.config.harnesses = state.config.harnesses.filter(item => item !== harness);
          delete notes[harness];
        });
    });
    onAction(panel, 'catalog', () => loadCatalog(harness));
    showCatalog(panel, harness);
    panel.querySelector('.models').replaceChildren(...models.map(entry => {
      const item = document.createElement('li');
      const label = document.createElement('span');
      label.textContent = modelLabel(entry.model);
      const remove = document.createElement('button');
      remove.type = 'button';
      remove.textContent = 'Remove model';
      remove.setAttribute('aria-label', `Remove ${label.textContent}`);
      remove.addEventListener('click', () => confirmRemoval(`Remove ${label.textContent}?`,
        'Candidate rows for this model will be removed.',
        candidate => candidate.harness === harness && candidate.model === entry.model));
      const details = document.createElement('details');
      details.className = 'family';
      details.open = Boolean(entry.family);
      const summary = document.createElement('summary');
      summary.textContent = familySummary(entry);
      summary.dataset.model = entry.model ?? '';
      const familyLabel = document.createElement('label');
      familyLabel.textContent = 'Override model family';
      const family = document.createElement('input');
      family.value = entry.family ?? '';
      family.placeholder = families.get(entry.model) || 'Unknown';
      family.dataset.model = entry.model ?? '';
      family.addEventListener('input', () => {
        if (family.value.trim()) entry.family = family.value.trim();
        else delete entry.family;
        summary.textContent = familySummary(entry);
      });
      family.addEventListener('change', () => renderRules());
      familyLabel.append(family);
      details.append(summary, familyLabel);
      item.append(label, remove, details);
      return item;
    }));
    return panel;
  }));
  if (focus) harnessPanel(focus).querySelector('.new-model').focus();
  changed();
}

function renderRules(focus) {
  const count = state.config.rules.length;
  rules.replaceChildren(...state.config.rules.map((rule, position) => {
    const number = position + 1;
    const panel = ruleTemplate.content.firstElementChild.cloneNode(true);
    const title = panel.querySelector('.rule-title');
    const heading = () => `${number}. ${rule.name || 'New rule'}`;
    title.textContent = heading();
    const name = connectField(panel, rule, 'name');
    name.addEventListener('input', () => { title.textContent = heading(); });
    connectField(panel, rule, 'description');
    const up = onAction(panel, 'up', () => { swap(state.config.rules, position, -1); renderRules(rule); });
    up.disabled = position === 0;
    up.setAttribute('aria-label', `Move rule ${number} up`);
    const down = onAction(panel, 'down', () => { swap(state.config.rules, position, 1); renderRules(rule); });
    down.disabled = position === count - 1;
    down.setAttribute('aria-label', `Move rule ${number} down`);
    onAction(panel, 'remove', async () => {
      const candidates = rule.candidates.length;
      const description = `“${rule.name || 'New rule'}”, its task description, and ${candidates} `
        + `candidate${candidates === 1 ? '' : 's'} will be removed.`;
      if (!await ask(`Remove rule ${number}?`, description, [], 'Remove rule')) return;
      state.config.rules.splice(state.config.rules.indexOf(rule), 1);
      renderRules();
    }).setAttribute('aria-label', `Remove rule ${number}`);
    onAction(panel, 'add-candidate', () => {
      const key = entry => JSON.stringify([entry.harness, entry.model]);
      const used = new Set(rule.candidates.map(key));
      const {harness, model} = state.config.pool.find(entry => !used.has(key(entry))) ?? state.config.pool[0];
      rule.candidates.push({harness, model, effort: 'default', role: 'both'});
      renderRules(rule.candidates.at(-1));
    }).disabled = !state.config.pool.length;
    const empty = panel.querySelector('.empty-rule');
    empty.hidden = rule.candidates.length !== 0;
    empty.textContent = state.config.pool.length ? 'Add a candidate to dispatch work under this rule.'
      : 'Add a model to the Harness Pool to choose candidates.';
    panel.querySelector('.candidates-hint').hidden = rule.candidates.length < 2;
    panel.querySelector('.candidates').replaceChildren(...rule.candidates.map((candidate, index) => {
      const row = candidateTemplate.content.firstElementChild.cloneNode(true);
      row.querySelector('legend').textContent = `Candidate ${index + 1}`;
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
        if (!state.efforts[entry.harness].includes(candidate.effort)) candidate.effort = 'default';
        renderRules(candidate);
      });
      options(row.querySelector('[name="effort"]'), state.efforts[candidate.harness]);
      candidate.role ??= 'both';
      for (const field of ['effort', 'role']) connectField(row, candidate, field);
      const move = offset => { swap(rule.candidates, index, offset); renderRules(candidate); };
      const up = onAction(row, 'up', () => move(-1));
      up.disabled = index === 0;
      up.setAttribute('aria-label', `Move candidate ${index + 1} of rule ${number} up`);
      const down = onAction(row, 'down', () => move(1));
      down.disabled = index === rule.candidates.length - 1;
      down.setAttribute('aria-label', `Move candidate ${index + 1} of rule ${number} down`);
      onAction(row, 'remove-candidate', () => {
        rule.candidates.splice(index, 1);
        renderRules(rule);
      }).setAttribute('aria-label', `Remove candidate ${index + 1} of rule ${number}`);
      if (candidate === focus) model.setAttribute('data-focus', '');
      return row;
    }));
    if (rule === focus) name.setAttribute('data-focus', '');
    return panel;
  }));
  rules.querySelector('[data-focus]')?.focus();
  changed();
}

function payload() {
  return {config: state.config, revision: state.revision};
}

async function refreshPreview() {
  const id = ++previewRequest;
  if (!editor.checkValidity()) {
    showStatus('Fill in every rule name and task description to update the preview.');
    return;
  }
  try {
    const data = await request('preview', payload());
    if (id !== previewRequest) return;
    preview.textContent = data.markdown;
    delete preview.dataset.stale;
    showStatus('');
  } catch (error) {
    if (id === previewRequest) showStatus(error.message, true);
  }
}

async function save() {
  if (!editor.reportValidity()) return;
  clearTimeout(previewTimer);
  previewRequest++;
  saveButton.disabled = stopEditor.disabled = editor.inert = true;
  try {
    let data;
    try {
      data = await request('save', payload());
    } catch (error) {
      if (error.status !== 409) throw error;
      const overwrite = await ask('Project files changed',
        `${state.policy} or the routing settings changed after the editor loaded them. `
        + 'Overwrite them with your edits, or cancel and reload the editor to see the changes.', [], 'Overwrite');
      if (!overwrite) {
        showStatus(`${error.message} Reload the editor to see the changes.`, true);
        return;
      }
      state.revision = (await request('state')).revision;
      data = await request('save', payload());
    }
    preview.textContent = data.markdown;
    delete preview.dataset.stale;
    state.revision = data.revision;
    savedConfig = JSON.stringify(state.config);
    unsaved.hidden = true;
    migration.hidden = true;
    showStatus(`Saved to ${state.policy}.`);
  } catch (error) {
    showStatus(error.message, true);
  } finally {
    saveButton.disabled = stopEditor.disabled = editor.inert = false;
  }
}

stopEditor.addEventListener('click', async () => {
  if (savedConfig !== undefined && dirty() && !await ask('Stop the editor?', 'Unsaved changes will be lost.', [], 'Stop editor')) return;
  stopEditor.disabled = editor.inert = true;
  try {
    await request('close', {});
    stopEditor.hidden = workspace.hidden = true;
    document.querySelector('#editor-stopped').hidden = false;
  } catch (error) {
    showStatus(error.message, true);
    stopEditor.disabled = editor.inert = false;
  }
});

addHarness.addEventListener('click', () => {
  const harness = availableHarness.value;
  state.config.harnesses.push(harness);
  renderPool(harness);
  renderNotes();
});
projectNotes.addEventListener('input', () => { state.config.launch_notes.project = projectNotes.value; });
preferReviewer.addEventListener('input', () => { state.config.prefer_independent_reviewer = preferReviewer.checked; });
addRule.addEventListener('click', () => {
  const rule = {name: '', description: '', candidates: []};
  state.config.rules.push(rule);
  renderRules(rule);
});
editor.addEventListener('input', changed);
editor.addEventListener('keydown', event => {
  if (event.key === 'Enter' && event.target instanceof HTMLInputElement) event.preventDefault();
});
editor.addEventListener('submit', event => {
  event.preventDefault();
  save();
});
document.addEventListener('keydown', event => {
  if (!(event.ctrlKey || event.metaKey) || event.key.toLowerCase() !== 's') return;
  event.preventDefault();
  if (!saveButton.disabled && !removeDialog.open) editor.requestSubmit();
});
window.addEventListener('beforeunload', event => {
  if (savedConfig === undefined || workspace.hidden || !dirty()) return;
  event.preventDefault();
  event.returnValue = '';
});

async function load() {
  try {
    state = await request('state');
    stopEditor.hidden = !state.background;
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
    savedConfig = JSON.stringify(state.config);
    saveButton.disabled = addRule.disabled = false;
    await refreshPreview();
  } catch (error) {
    if (error.data?.background) stopEditor.hidden = false;
    showStatus(error.message, true);
  }
}

load();
