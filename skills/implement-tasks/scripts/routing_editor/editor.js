const $ = selector => document.querySelector(selector);
const editor = $('#editor');
const workspace = $('#workspace');
const saveButton = $('#save-button');
const unsaved = $('#unsaved');
const status = $('#status');
const preview = $('#preview');
const stopEditor = $('#stop-editor');
const rules = $('#rules');
const addRule = $('#add-rule');
const pool = $('#pool');
const availableHarness = $('#available-harness');
const removeDialog = $('#remove-dialog');
const confirmAction = $('#confirm-action');
const projectNotes = $('#project-notes');
const preferReviewer = $('#prefer-reviewer');
const migration = $('#migration');
const drawer = $('#drawer');
const markdownButton = $('#toggle-markdown');
const DEFAULT_MODEL = 'Harness default';
const catalogs = new Map();
const catalogStatus = new Map();
const catalogEfforts = new Map();
const loadingCatalogs = new Set();
const families = new Map();
const collapsed = new Set();
const openNotes = new Set();
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
  status.textContent = status.title = message;
  status.dataset.error = String(error);
}

function clone(selector) {
  return $(selector).content.firstElementChild.cloneNode(true);
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function options(select, items) {
  select.replaceChildren(...items.map(item => new Option(item, item)));
}

function onAction(root, action, handler) {
  const button = root.querySelector(`[data-action="${action}"]`);
  button.addEventListener('click', handler);
  return button;
}

function labelled(button, label) {
  button.setAttribute('aria-label', label);
  button.title = label;
  return button;
}

function connectField(root, object, property) {
  const input = root.querySelector(`[name="${property}"]`);
  input.value = object[property];
  input.addEventListener('input', () => { object[property] = input.value; });
  return input;
}

function modelLabel(model) {
  return model ?? DEFAULT_MODEL;
}

function modelFamily(entry) {
  return entry.family || families.get(entry.model);
}

function allowedEfforts(entry) {
  if (entry.efforts?.length) return ['default', ...entry.efforts];
  if (entry.harness === 'agy' && /-(?:low|medium|high|xhigh|max|ultra)$/.test(entry.model ?? '')) return ['default'];
  return state.efforts[entry.harness];
}

function poolEntry(candidate) {
  return state.config.pool.find(entry => entry.harness === candidate.harness && entry.model === candidate.model);
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

function setDrawer(open) {
  drawer.hidden = !open;
  markdownButton.setAttribute('aria-expanded', String(open));
}

function ask(title, description, items, action) {
  $('#remove-title').textContent = title;
  $('#remove-description').textContent = description;
  $('#affected-rules').replaceChildren(...items.map(text => element('li', '', text)));
  confirmAction.textContent = action;
  removeDialog.returnValue = '';
  removeDialog.showModal();
  return new Promise(resolve => removeDialog.addEventListener('close',
    () => resolve(removeDialog.returnValue === 'remove'), {once: true}));
}

async function removeFromPool(title, description, includes, remove, keepsData = false) {
  const affected = state.config.rules.filter(rule => rule.candidates.some(includes));
  const items = affected.map(rule =>
    `${rule.name || 'Unnamed rule'}${rule.candidates.every(includes) ? ' (will need a Candidate)' : ''}`);
  if (affected.length || keepsData) {
    const text = affected.length ? `${description} These rules will be affected.` : description;
    if (!await ask(title, text, items, 'Remove')) return;
  }
  for (const rule of affected) rule.candidates = rule.candidates.filter(candidate => !includes(candidate));
  state.config.pool = state.config.pool.filter(model => !includes(model));
  remove?.();
  renderPool();
  renderRules();
}

function harnessPanel(harness) {
  return [...pool.children].find(panel => panel.dataset.harness === harness);
}

function showCatalog(panel, harness) {
  const inPool = new Set(state.config.pool.filter(entry => entry.harness === harness).map(entry => entry.model));
  const suggestions = (catalogs.get(harness) ?? []).filter(model => !inPool.has(model));
  options(panel.querySelector('datalist'), inPool.has(null) ? suggestions : [DEFAULT_MODEL, ...suggestions]);
  panel.querySelector('.catalog-status').textContent = catalogStatus.get(harness) ?? '';
  panel.querySelector('[data-action="catalog"]').disabled = loadingCatalogs.has(harness);
}

async function loadCatalog(harness) {
  loadingCatalogs.add(harness);
  catalogStatus.set(harness, 'Loading models…');
  const sync = () => { const panel = harnessPanel(harness); if (panel) showCatalog(panel, harness); };
  sync();
  try {
    const {models: ids, families: known, efforts} = await request(`catalog/${harness}`);
    catalogs.set(harness, ids);
    catalogEfforts.set(harness, efforts);
    for (const [id, family] of Object.entries(known)) families.set(id, family);
    catalogStatus.set(harness, ids.length ? `${ids.length} models in suggestions.`
      : 'No catalog. Type an exact model ID.');
  } catch (error) {
    catalogStatus.set(harness, error.message);
  } finally {
    loadingCatalogs.delete(harness);
    sync();
  }
}

function familyBadge(badge, entry) {
  const detected = families.get(entry.model);
  badge.textContent = entry.family || detected || '?';
  badge.classList.toggle('override', Boolean(entry.family));
  labelled(badge, entry.family ? `Model Family override for ${modelLabel(entry.model)}`
    : `${detected ? 'Detected' : 'Unknown'} Model Family for ${modelLabel(entry.model)}. Click to override.`);
}

function modelRow(harness, entry) {
  const item = element('li');
  const label = modelLabel(entry.model);
  const name = element('span', entry.model === null ? 'model-id default' : 'model-id', label);
  name.title = `Efforts: ${allowedEfforts(entry).join(', ')}`;
  const badge = element('button', 'badge');
  badge.type = 'button';
  familyBadge(badge, entry);
  const remove = labelled(element('button', 'icon reveal', '✕'), `Remove ${label}`);
  remove.type = 'button';
  const family = element('input', 'family-input');
  family.hidden = true;
  family.value = entry.family ?? '';
  family.placeholder = families.get(entry.model) || 'Unknown Model Family';
  family.setAttribute('aria-label', `Model Family for ${label}`);
  badge.addEventListener('click', () => {
    family.hidden = !family.hidden;
    if (!family.hidden) family.focus();
  });
  family.addEventListener('input', () => {
    if (family.value.trim()) entry.family = family.value.trim();
    else delete entry.family;
    familyBadge(badge, entry);
  });
  family.addEventListener('change', () => renderRules());
  family.addEventListener('keydown', event => {
    if (event.key !== 'Enter' && event.key !== 'Escape') return;
    event.preventDefault();
    family.hidden = true;
    badge.focus();
  });
  remove.addEventListener('click', () => removeFromPool(`Remove ${label}?`,
    'Candidate rows for this model will be removed.',
    candidate => candidate.harness === harness && candidate.model === entry.model));
  item.append(name, badge, remove, family);
  return item;
}

function harnessGroup(harness) {
  const panel = clone('#harness-template');
  const notes = state.config.launch_notes.harnesses;
  const models = state.config.pool.filter(entry => entry.harness === harness);
  panel.dataset.harness = harness;
  panel.open = !collapsed.has(harness);
  panel.addEventListener('toggle', () => { if (panel.open) collapsed.delete(harness); else collapsed.add(harness); });
  panel.querySelector('.harness-title').textContent = harness;
  const list = panel.querySelector('datalist');
  const input = panel.querySelector('.new-model');
  list.id = `catalog-${harness}`;
  input.setAttribute('list', list.id);
  input.setAttribute('aria-label', `Add a ${harness} model`);
  input.addEventListener('focus', () => { if (!catalogStatus.has(harness)) loadCatalog(harness); });
  const add = async () => {
    const value = input.value.trim();
    const model = value === DEFAULT_MODEL ? null : value;
    const message = panel.querySelector('.catalog-status');
    if (model === '' || models.some(entry => entry.model === model)) {
      message.textContent = model === '' ? 'Type a model ID, then press Enter.' : 'This model is already in the pool.';
      return;
    }
    const levels = model && catalogEfforts.get(harness)?.[model];
    state.config.pool.push(levels ? {harness, model, efforts: levels} : {harness, model});
    renderPool(harness);
    renderRules();
    if (model === null || families.has(model)) return;
    try {
      const {family} = await request('family', {model});
      families.set(model, family);
      const active = document.activeElement.closest?.('.harness')?.dataset.harness;
      renderPool(document.activeElement.matches('.new-model') ? active : undefined);
      renderRules();
    } catch (error) {
      showStatus(error.message, true);
    }
  };
  input.addEventListener('keydown', event => {
    if (event.key !== 'Enter') return;
    event.preventDefault();
    add();
  });
  input.addEventListener('input', event => {
    if (event.inputType === 'insertReplacementText' || event.inputType === undefined) add();
  });
  labelled(onAction(panel, 'catalog', () => loadCatalog(harness)), `Reload ${harness} models`);
  labelled(onAction(panel, 'remove-harness', () => {
    const note = Boolean(notes[harness]);
    const extra = note ? ' Its Launch Note will be removed too.' : '';
    removeFromPool(`Remove ${harness}?`, `Candidate rows for this Harness will be removed.${extra}`,
      entry => entry.harness === harness, () => {
        state.config.harnesses = state.config.harnesses.filter(item => item !== harness);
        delete notes[harness];
      }, note);
  }), `Remove ${harness}`);
  showCatalog(panel, harness);
  panel.querySelector('.models').replaceChildren(...models.map(entry => modelRow(harness, entry)));
  const noteBox = panel.querySelector('.note');
  const note = noteBox.querySelector('textarea');
  const dot = noteBox.querySelector('.dot');
  note.value = notes[harness] ?? '';
  note.setAttribute('aria-label', `${harness} Launch Note`);
  dot.hidden = !note.value;
  noteBox.open = openNotes.has(harness);
  noteBox.addEventListener('toggle', () => { if (noteBox.open) openNotes.add(harness); else openNotes.delete(harness); });
  note.addEventListener('input', () => {
    if (note.value) notes[harness] = note.value;
    else delete notes[harness];
    dot.hidden = !note.value;
  });
  return panel;
}

function renderPool(focus) {
  if (focus) collapsed.delete(focus);
  const choices = state.harnesses.filter(harness => !state.config.harnesses.includes(harness));
  availableHarness.replaceChildren(new Option('+ Harness', ''), ...choices.map(harness => new Option(harness, harness)));
  availableHarness.hidden = !choices.length;
  availableHarness.classList.toggle('attention', !state.config.pool.length);
  pool.replaceChildren(...state.config.harnesses.map(harnessGroup));
  if (focus) harnessPanel(focus).querySelector('.new-model').focus();
  changed();
}

function candidateRow(rule, number, candidate, index, focus) {
  const row = clone('#candidate-template');
  const place = `Candidate ${index + 1} of rule ${number}`;
  row.setAttribute('aria-label', place);
  const model = row.querySelector('[name="model"]');
  state.config.pool.forEach((entry, position) => {
    const selected = entry.harness === candidate.harness && entry.model === candidate.model;
    const family = modelFamily(entry);
    const label = `${entry.harness} · ${modelLabel(entry.model)}${family ? ` · ${family}` : ''}`;
    model.add(new Option(label, position, selected, selected));
  });
  model.addEventListener('input', () => {
    const entry = state.config.pool[model.value];
    candidate.harness = entry.harness;
    candidate.model = entry.model;
    if (!allowedEfforts(entry).includes(candidate.effort)) candidate.effort = 'default';
    renderRules(candidate);
  });
  options(row.querySelector('[name="effort"]'), allowedEfforts(poolEntry(candidate)));
  connectField(row, candidate, 'effort');
  candidate.role ??= 'both';
  for (const radio of row.querySelectorAll('.segmented input')) {
    radio.name = `role-${number}-${index}`;
    radio.checked = radio.value === candidate.role;
    radio.addEventListener('input', () => { candidate.role = radio.value; });
  }
  const move = offset => { swap(rule.candidates, index, offset); renderRules(candidate); };
  labelled(onAction(row, 'up', () => move(-1)), `Move ${place} up`).disabled = index === 0;
  labelled(onAction(row, 'down', () => move(1)), `Move ${place} down`).disabled = index === rule.candidates.length - 1;
  labelled(onAction(row, 'remove-candidate', () => {
    rule.candidates.splice(index, 1);
    renderRules(rule);
  }), `Remove ${place}`);
  if (candidate === focus) model.setAttribute('data-focus', '');
  return row;
}

function renderRules(focus) {
  const count = state.config.rules.length;
  rules.replaceChildren(...state.config.rules.map((rule, position) => {
    const number = position + 1;
    const panel = clone('#rule-template');
    panel.querySelector('.rule-number').textContent = number;
    const name = connectField(panel, rule, 'name');
    connectField(panel, rule, 'description');
    labelled(onAction(panel, 'up', () => { swap(state.config.rules, position, -1); renderRules(rule); }),
      `Move rule ${number} up`).disabled = position === 0;
    labelled(onAction(panel, 'down', () => { swap(state.config.rules, position, 1); renderRules(rule); }),
      `Move rule ${number} down`).disabled = position === count - 1;
    labelled(onAction(panel, 'remove', async () => {
      const candidates = rule.candidates.length;
      if (candidates) {
        const text = `“${rule.name || 'Unnamed rule'}” and its ${candidates} Candidate${candidates === 1 ? '' : 's'} will be removed.`;
        if (!await ask(`Remove rule ${number}?`, text, [], 'Remove rule')) return;
      }
      state.config.rules.splice(state.config.rules.indexOf(rule), 1);
      renderRules();
    }), `Remove rule ${number}`);
    const add = onAction(panel, 'add-candidate', () => {
      const key = entry => JSON.stringify([entry.harness, entry.model]);
      const used = new Set(rule.candidates.map(key));
      const {harness, model} = state.config.pool.find(entry => !used.has(key(entry))) ?? state.config.pool[0];
      rule.candidates.push({harness, model, effort: 'default', role: 'both'});
      renderRules(rule.candidates.at(-1));
    });
    add.hidden = !state.config.pool.length;
    const empty = panel.querySelector('.empty-rule');
    empty.hidden = rule.candidates.length !== 0;
    empty.textContent = state.config.pool.length ? 'No Candidates yet.'
      : 'Add models to the Harness Pool to choose Candidates.';
    panel.querySelector('.candidates').replaceChildren(
      ...rule.candidates.map((candidate, index) => candidateRow(rule, number, candidate, index, focus)));
    if (rule === focus) name.setAttribute('data-focus', '');
    return panel;
  }));
  rules.querySelector('[data-focus]')?.focus();
  changed();
}

function renderProjectNote() {
  projectNotes.value = state.config.launch_notes.project;
  $('.project-note .dot').hidden = !projectNotes.value;
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
    workspace.hidden = $('#top-actions').hidden = true;
    $('#editor-stopped').hidden = false;
  } catch (error) {
    showStatus(error.message, true);
    stopEditor.disabled = editor.inert = false;
  }
});

availableHarness.addEventListener('change', () => {
  const harness = availableHarness.value;
  if (!harness) return;
  state.config.harnesses.push(harness);
  renderPool(harness);
});
markdownButton.addEventListener('click', () => setDrawer(drawer.hidden));
$('#close-drawer').addEventListener('click', () => { setDrawer(false); markdownButton.focus(); });
projectNotes.addEventListener('input', () => {
  state.config.launch_notes.project = projectNotes.value;
  $('.project-note .dot').hidden = !projectNotes.value;
});
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
  if (event.key === 'Escape' && !drawer.hidden && !removeDialog.open) {
    setDrawer(false);
    return;
  }
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
    $('#project').textContent = state.project;
    state.config.launch_notes ??= {project: '', harnesses: {}};
    state.config.launch_notes.project ??= '';
    state.config.launch_notes.harnesses ??= {};
    state.config.harnesses ??= [...new Set(state.config.pool.map(entry => entry.harness))];
    for (const harness of Object.keys(state.config.launch_notes.harnesses)) {
      if (!state.config.harnesses.includes(harness)) state.config.harnesses.push(harness);
    }
    for (const [id, family] of Object.entries(state.families)) families.set(id, family);
    preferReviewer.checked = state.config.prefer_independent_reviewer ?? true;
    $('#handwritten').textContent = state.handwritten;
    migration.hidden = !state.handwritten;
    setDrawer(Boolean(state.handwritten));
    renderPool();
    renderRules();
    renderProjectNote();
    savedConfig = JSON.stringify(state.config);
    saveButton.disabled = addRule.disabled = false;
    await refreshPreview();
  } catch (error) {
    if (error.data?.background) stopEditor.hidden = false;
    showStatus(error.message, true);
  }
}

load();
