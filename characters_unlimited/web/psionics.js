'use strict';
let psionicSequence = 0, psionicReady = false;
function setPsionicsBusy() {
  document.querySelectorAll('#psionics-panel button, #psionics-panel input, #psionics-panel select')
    .forEach(element => element.disabled = navigationBusy || !psionicReady || element.dataset.retained === 'yes');
}
async function savePsionics(choices) {
  if (navigationBusy || !psionicReady) return;
  lockNavigation(true);
  try {
    await flushSave();
    const result = await request(`/api/characters/${current.id}/psionics`, {revision:current.revision, ...choices});
    render(result);
  } catch (error) { showError(error); }
  finally { lockNavigation(false); }
}
async function loadPsionics(character) {
  const sequence = ++psionicSequence;
  let panel = $('psionics-panel');
  if (!panel) {
    panel = document.createElement('section'); panel.id = 'psionics-panel'; panel.className = 'panel';
    $('resources-panel').after(panel);
  }
  panel.hidden = character.game !== 'rifts';
  psionicReady = false; setPsionicsBusy();
  if (panel.hidden) return;
  panel.textContent = 'Loading natural psionics…';
  const view = await request(`/api/characters/${character.id}/psionics`);
  if (current.id !== character.id || sequence !== psionicSequence) return;
  panel.innerHTML = '<div class="section-title"><h2>Natural psionics</h2><span class="tag">RIFTS</span></div><p id="psionic-status"></p><button type="button" id="psionic-roll">Roll psionic potential</button> <button type="button" id="psionic-skip">Skip psionics</button><form id="psionic-form"><label>Selection mode<select id="psionic-mode"></select></label><fieldset id="psionic-categories"><legend>Power categories</legend></fieldset><p id="psionic-counts" class="help"></p><button type="submit">Save psionic choices</button><label>Find a power<input type="search" id="psionic-search"></label><div id="psionic-options"></div></form>';
  const state = view.state;
  const enabled = state?.enabled;
  const amounts = Object.values(view.resources).map(row => `${row.name}: ${row.value}`).join(' · ');
  $('psionic-status').textContent = state
    ? `${view.path} · potential ${state.face ?? 'not rolled'} · ${enabled ? 'enabled' : 'skipped'} · psychic save target ${view.save_target} before attribute/class bonuses${amounts ? ' · ' + amounts : ''}`
    : 'Optional: roll once for natural psychic potential or skip this step. Rolls are retained when choices change.';
  $('psionic-roll').dataset.retained = state?.face != null ? 'yes' : 'no';
  $('psionic-roll').onclick = () => savePsionics({roll:true, enabled:true});
  $('psionic-skip').onclick = () => savePsionics({enabled:false});
  $('psionic-mode').replaceChildren(...(view.modes || ['single']).map(mode => {
    const option = document.createElement('option'); option.value = mode;
    option.textContent = mode === 'single' ? 'One category' : 'Two or three categories'; return option;
  }));
  $('psionic-mode').value = state?.mode || 'single';
  for (const category of view.categories) {
    const label = document.createElement('label');
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = category;
    input.checked = state?.categories.includes(category) || false;
    label.append(input, document.createTextNode(category)); $('psionic-categories').append(label);
  }
  $('psionic-counts').textContent = (view.guidance || []).join(' ') + ' Counts and category eligibility are guidance for your table.';
  for (const ability of view.catalog) {
    const details = document.createElement('details');
    details.dataset.search = `${ability.name} ${ability.tags.join(' ')}`.toLowerCase();
    const summary = document.createElement('summary');
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = ability.id;
    input.checked = state?.abilities.selections.includes(ability.id) || false;
    input.setAttribute('aria-label', `Select ${ability.name}`);
    input.onclick = event => event.stopPropagation();
    summary.append(input, document.createTextNode(` ${ability.name} · ${ability.tags.join(', ')}`));
    const text = document.createElement('p'); text.textContent = ability.description;
    const metadata = document.createElement('p'); metadata.className = 'help';
    metadata.textContent = (ability.parameters || []).map(row => `${row.name}: ${row.text}`).join(' · ');
    const source = document.createElement('p'); source.className = 'help';
    source.textContent = `${ability.source.book} · ${ability.source.section}`;
    details.append(summary, text, metadata, source); $('psionic-options').append(details);
  }
  $('psionic-search').oninput = () => {
    const query = $('psionic-search').value.toLowerCase().trim();
    document.querySelectorAll('#psionic-options details').forEach(row => row.hidden = !row.dataset.search.includes(query));
  };
  $('psionic-form').onsubmit = event => {
    event.preventDefault();
    savePsionics({enabled:true, mode:$('psionic-mode').value,
      categories:[...document.querySelectorAll('#psionic-categories input:checked')].map(row => row.value),
      selections:[...document.querySelectorAll('#psionic-options input:checked')].map(row => row.value)});
  };
  psionicReady = true; setPsionicsBusy();
}
