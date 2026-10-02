'use strict';
let token, current, characters = [], saveTimer, savePromise, navigationBusy = false, coverage;
const $ = id => document.getElementById(id);
async function request(path, data) {
  const response = await fetch(path, data === undefined ? {} : {method:'POST', headers:{'Content-Type':'application/json','X-Session-Token':token}, body:JSON.stringify(data)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || 'Request failed');
  return result;
}
function showError(error) { $('error').textContent = error.message; $('error').hidden = false; $('save-status').textContent = 'Check the message below'; }
function lockNavigation(busy) {
  navigationBusy = busy;
  ['name', 'notes', 'new-character', 'source-coverage', 'reroll-ones', 'extra-die', 'reroll-all', 'roll-history'].forEach(id => $(id).disabled = busy);
  document.querySelectorAll('#library button, .attribute button').forEach(button => button.disabled = busy);
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button').forEach(element => element.disabled = busy || !skillsReady);
}
function library() {
  $('library').replaceChildren();
  characters.forEach(character => {
    const button = document.createElement('button');
    button.textContent = character.name || 'Unnamed adventurer';
    button.classList.toggle('selected', current?.id === character.id);
    button.disabled = navigationBusy;
    button.onclick = async () => {
      if (navigationBusy) return;
      lockNavigation(true);
      try { await flushSave(); render(await request('/api/characters/' + character.id)); }
      catch(error) { showError(error); }
      finally { lockNavigation(false); }
    };
    $('library').append(button);
  });
}
function render(character) {
  const expanded = new Set([...document.querySelectorAll('.attribute[open]')].map(element => element.dataset.attribute));
  current = character;
  characters = [character, ...characters.filter(item => item.id !== character.id)];
  $('welcome').hidden = true; $('builder').hidden = false; $('error').hidden = true;
  $('coverage').hidden = true;
  $('name').value = character.name; $('notes').value = character.notes;
  $('summary-name').textContent = character.name || 'Unnamed adventurer';
  $('reroll-ones').checked = character.generation?.reroll_ones || false;
  $('extra-die').checked = character.generation?.extra_die || false;
  $('attributes').replaceChildren();
  Object.entries(character.attributes).forEach(([name, attribute]) => {
    const detail = document.createElement('details'); detail.className = 'attribute'; detail.dataset.attribute = name; detail.open = expanded.has(name);
    const heading = document.createElement('summary'); heading.textContent = name;
    const value = document.createElement('strong'); value.textContent = attribute.value; heading.append(value);
    const explanation = document.createElement('p');
    explanation.textContent = `Dice: ${attribute.rolls.join(' + ')}${attribute.discarded?.length ? '; dropped: ' + attribute.discarded.join(' + ') : ''}${attribute.bonus_rolls.length ? '; exceptional: ' + attribute.bonus_rolls.join(' + ') : ''}. Base: ${attribute.base}. ${attribute.explanation.source.book} — ${attribute.explanation.source.section}`;
    const edit = document.createElement('button'); edit.textContent = `Edit ${name}`; edit.disabled = navigationBusy;
    edit.onclick = () => {
      $('attribute-title').textContent = `Edit ${name}`; $('editing-attribute').value = name;
      $('attribute-mode').value = attribute.fixed != null ? 'fixed' : attribute.adjustment ? 'adjustment' : 'calculated';
      updateAttributeMode(); $('attribute-error').hidden = true; $('attribute-dialog').showModal();
    };
    const reroll = document.createElement('button'); reroll.textContent = `Reroll ${name}`; reroll.disabled = navigationBusy;
    reroll.onclick = () => characterAction('reroll', {attribute:name, generation:rollSettings()}).catch(showError);
    detail.append(heading, explanation, edit, reroll); $('attributes').append(detail);
  });
  $('completion').replaceChildren(...character.completion.map(message => { const item = document.createElement('li'); item.textContent = message; return item; }));
  $('save-status').textContent = 'Saved on this PC'; library();
  loadSkills(character).catch(showError);
}
let skillsReady = false, skillLoadSequence = 0;
async function loadSkills(character) {
  const sequence = ++skillLoadSequence;
  skillsReady = false;
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button').forEach(element => element.disabled = true);
  const view = await request(`/api/characters/${character.id}/skills`);
  if (current.id !== character.id || sequence !== skillLoadSequence) return;
  $('skill-choice').replaceChildren(...view.catalog.map(skill => { const option = document.createElement('option'); option.value = skill.id; option.textContent = skill.name; return option; }));
  $('skill-counts').textContent = Object.entries(view.remaining).map(([pool, count]) => `${pool}: ${count} remaining`).join(' · ');
  $('skill-list').replaceChildren(...[...view.grants.map(skill => ({...skill, grant:true})), ...view.selected].map((skill, index) => {
    const row = document.createElement('details'); const heading = document.createElement('summary');
    heading.textContent = `${skill.name}${skill.specialty ? ' — ' + skill.specialty : ''}: ${skill.percentage}% · ${skill.grant ? 'O.C.C. grant' : skill.pool} · ${skill.quality}`;
    const explanation = document.createElement('p'); explanation.className = 'help';
    explanation.textContent = Object.entries(skill.contributions).map(([name, amount]) => `${name.replaceAll('_', ' ')} ${amount}%`).join(' + ') + ` · ${skill.source.book}, pp. ${skill.source.pages.join(', ')}`;
    row.append(heading, explanation);
    if (!skill.grant) {
      const remove = document.createElement('button'); remove.textContent = 'Remove selection';
      remove.onclick = () => characterAction('skills', {selections:(current.skill_selections || []).filter((item, position) => position !== index - view.grants.length)}).catch(showError);
      row.append(remove);
    }
    return row;
  }));
  for (const [id, items] of [['skill-warnings', view.warnings], ['skill-gaps', [...view.gaps, ...view.sources]]]) {
    $(id).replaceChildren(...items.map(message => { const item = document.createElement('li'); item.textContent = message; return item; }));
  }
  skillsReady = true;
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button').forEach(element => element.disabled = navigationBusy);
}
$('skill-form').onsubmit = async event => {
  event.preventDefault();
  if (!skillsReady || navigationBusy) return;
  await characterAction('skills', {selections:[...(current.skill_selections || []), {skill_id:$('skill-choice').value, pool:$('skill-pool').value, specialty:$('skill-specialty').value}]}).catch(showError);
};
async function flushSave() {
  clearTimeout(saveTimer);
  if (savePromise) return savePromise;
  savePromise = (async () => {
    while (current && ($('name').value !== current.name || $('notes').value !== current.notes)) {
      $('save-status').textContent = 'Saving…';
      const changes = {revision: current.revision ?? 0};
      if ($('name').value !== current.name) changes.name = $('name').value;
      if ($('notes').value !== current.notes) changes.notes = $('notes').value;
      const saved = await request('/api/characters/' + current.id, changes);
      current = saved; characters = [saved, ...characters.filter(item => item.id !== saved.id)];
      $('summary-name').textContent = saved.name || 'Unnamed adventurer'; library();
    }
    $('save-status').textContent = 'Saved on this PC';
  })();
  try { await savePromise; } finally { savePromise = null; }
}
['name','notes'].forEach(id => $(id).oninput = () => { $('save-status').textContent = 'Unsaved changes'; clearTimeout(saveTimer); saveTimer = setTimeout(() => flushSave().catch(showError), 400); });
window.addEventListener('beforeunload', event => { if (current && ($('name').value !== current.name || $('notes').value !== current.notes)) { event.preventDefault(); event.returnValue = ''; } });
const start = async () => { try { await flushSave(); $('new-dialog').showModal(); } catch(error) { showError(error); } };
$('start').onclick = start; $('new-character').onclick = start;
$('cancel').onclick = () => $('new-dialog').close();
function rollSettings() { return {reroll_ones:$('reroll-ones').checked, extra_die:$('extra-die').checked}; }
async function characterAction(action, data) {
  if (navigationBusy) return;
  lockNavigation(true);
  try { await flushSave(); render(await request(`/api/characters/${current.id}/${action}`, {...data, revision:current.revision ?? 0})); }
  finally { lockNavigation(false); }
}
$('reroll-all').onclick = () => characterAction('reroll', {generation:rollSettings()}).catch(showError);
function updateAttributeMode() {
  const mode = $('attribute-mode').value;
  const attribute = current.attributes[$('editing-attribute').value];
  $('attribute-value').value = mode === 'adjustment' ? attribute.adjustment || 0 : attribute.value;
  const calculated = mode === 'calculated';
  $('attribute-value').disabled = calculated; $('attribute-value').required = !calculated;
}
$('attribute-mode').onchange = updateAttributeMode;
$('attribute-cancel').onclick = () => $('attribute-dialog').close();
$('attribute-form').onsubmit = async event => {
  event.preventDefault(); const button = event.submitter; button.disabled = true;
  try {
    const mode = $('attribute-mode').value;
    const value = mode === 'calculated' ? null : Number($('attribute-value').value);
    if (value !== null && !Number.isSafeInteger(value)) throw new Error('Enter a whole number within the supported numeric range');
    await characterAction('attribute', {attribute:$('editing-attribute').value, mode, value});
    $('attribute-dialog').close();
  } catch(error) { $('attribute-error').textContent = error.message; $('attribute-error').hidden = false; }
  finally { button.disabled = false; }
};
$('roll-history').onclick = () => {
  $('history-events').replaceChildren(...(current.roll_history || []).map(event => {
    const entry = document.createElement('details'); const title = document.createElement('summary');
    title.textContent = `${event.kind} · ${event.at ? new Date(event.at).toLocaleString() : 'Earlier saved rolls'}`;
    entry.append(title);
    for (const [name, value] of Object.entries(event.attributes)) {
      const settings = value.generation || event.generation;
      const options = settings ? ` · reroll ones: ${settings.reroll_ones ? 'yes' : 'no'} · extra die: ${settings.extra_die ? 'yes' : 'no'}` : '';
      const text = document.createElement('p'); text.className = 'help'; text.textContent = `${name}: base ${value.base} · dice ${value.rolls.join(', ')}${value.discarded?.length ? ' · dropped ' + value.discarded.join(', ') : ''}${value.bonus_rolls.length ? ' · exceptional ' + value.bonus_rolls.join(', ') : ''}${value.rerolls?.length ? ' · rerolled ones ' + value.rerolls.map(item => item.rolls.join(' → ')).join('; ') : ''}${options}`; entry.append(text);
    }
    return entry;
  }));
  $('history-dialog').showModal();
};
$('history-close').onclick = () => $('history-dialog').close();
function renderCoverageCandidates() {
  const query = $('coverage-search').value.toLowerCase();
  const matches = coverage.candidates.filter(item => `${item.title} ${item.book_id}`.toLowerCase().includes(query));
  $('coverage-count').textContent = `${matches.length} candidate sections. Showing the first 100; search to narrow results.`;
  $('coverage-candidates').replaceChildren(...matches.slice(0,100).map(item => {
    const entry = document.createElement('details'); entry.className = 'source-entry';
    const title = document.createElement('summary'); title.textContent = item.title;
    const description = document.createElement('p'); description.className = 'help';
    description.textContent = `${item.book_id} · Markdown lines ${item.line}–${item.end_line} · ${item.status}. Mechanical implementation and source review remain pending.`;
    entry.append(title,description); return entry;
  }));
}
$('coverage-search').oninput = renderCoverageCandidates;
$('source-coverage').onclick = async () => {
  if (navigationBusy) return;
  lockNavigation(true);
  try {
    await flushSave(); coverage = await request('/api/coverage');
    $('builder').hidden = true; $('welcome').hidden = true; $('coverage').hidden = false;
    $('coverage-summary').textContent = `${coverage.summary.books} books · ${coverage.summary.candidates} extracted sections · ${coverage.summary.books_reviewed} books reviewed · ${coverage.summary.fully_automated} fully automated options`;
    $('coverage-books').replaceChildren(...coverage.books.map(book => {
      const entry = document.createElement('section'); entry.className = 'panel';
      const title = document.createElement('h3'); title.textContent = book.filename.replace('.md','');
      const metadata = document.createElement('p'); metadata.className = 'help';
      metadata.textContent = `${book.candidate_count} sections · ${book.review_complete ? 'Reviewed' : 'Audit pending'} · ${book.original_pdf ? 'Original PDF recorded' : 'Original PDF not available'}`;
      const fingerprints = document.createElement('details');
      const fingerprintHeading = document.createElement('summary'); fingerprintHeading.textContent = 'Inspect source fingerprints';
      const markdownHash = document.createElement('p'); markdownHash.className = 'source-hash'; markdownHash.textContent = `Markdown: ${book.filename} · SHA-256 ${book.sha256}`;
      const pdfHash = document.createElement('p'); pdfHash.className = 'source-hash'; pdfHash.textContent = book.original_pdf ? `PDF: ${book.original_pdf} · SHA-256 ${book.pdf_sha256}` : 'No matching original PDF was found.';
      fingerprints.append(fingerprintHeading, markdownHash, pdfHash);
      entry.append(title,metadata,fingerprints); return entry;
    })); renderCoverageCandidates();
  } catch(error) { showError(error); } finally { lockNavigation(false); }
};
$('create-form').onsubmit = async event => { event.preventDefault(); const button = event.submitter; button.disabled = true; try { render(await request('/api/characters', {name:new FormData(event.target).get('name'), generation:{reroll_ones:$('new-reroll-ones').checked, extra_die:$('new-extra-die').checked}})); $('new-dialog').close(); event.target.reset(); } catch(error) { $('create-error').textContent = error.message; $('create-error').hidden = false; } finally { button.disabled = false; } };
request('/api/bootstrap').then(result => {
  token = result.token; characters = result.characters;
  const pack = result.catalog.packs[0];
  for (const [element, entries] of [[$('race'),pack.races],[$('character-class'),pack.classes]]) {
    entries.forEach(entry => { const option = document.createElement('option'); option.value = entry.id; option.textContent = entry.name; element.append(option); });
    element.disabled = true;
  }
  library();
}).catch(showError);
