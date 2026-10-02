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
  ['name', 'notes', 'new-character', 'source-coverage'].forEach(id => $(id).disabled = busy);
  document.querySelectorAll('#library button').forEach(button => button.disabled = busy);
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
  current = character;
  characters = [character, ...characters.filter(item => item.id !== character.id)];
  $('welcome').hidden = true; $('builder').hidden = false; $('error').hidden = true;
  $('coverage').hidden = true;
  $('name').value = character.name; $('notes').value = character.notes;
  $('summary-name').textContent = character.name || 'Unnamed adventurer';
  $('attributes').replaceChildren();
  Object.entries(character.attributes).forEach(([name, attribute]) => {
    const detail = document.createElement('details'); detail.className = 'attribute';
    const heading = document.createElement('summary'); heading.textContent = name;
    const value = document.createElement('strong'); value.textContent = attribute.value; heading.append(value);
    const explanation = document.createElement('p');
    explanation.textContent = `Dice: ${attribute.rolls.join(' + ')}${attribute.bonus_rolls.length ? '; exceptional: ' + attribute.bonus_rolls.join(' + ') : ''}. ${attribute.explanation.source.book} — ${attribute.explanation.source.section}`;
    detail.append(heading, explanation); $('attributes').append(detail);
  });
  $('completion').replaceChildren(...character.completion.map(message => { const item = document.createElement('li'); item.textContent = message; return item; }));
  $('save-status').textContent = 'Saved on this PC'; library();
}
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
$('create-form').onsubmit = async event => { event.preventDefault(); const button = event.submitter; button.disabled = true; try { render(await request('/api/characters', {name:new FormData(event.target).get('name')})); $('new-dialog').close(); event.target.reset(); } catch(error) { showError(error); } finally { button.disabled = false; } };
request('/api/bootstrap').then(result => {
  token = result.token; characters = result.characters;
  const pack = result.catalog.packs[0];
  for (const [element, entries] of [[$('race'),pack.races],[$('character-class'),pack.classes]]) {
    entries.forEach(entry => { const option = document.createElement('option'); option.value = entry.id; option.textContent = entry.name; element.append(option); });
    element.disabled = true;
  }
  library();
}).catch(showError);
