'use strict';
let psionicSequence = 0, psionicReady = false;
function setPsionicsBusy() {
  document.querySelectorAll('#psionics-panel button, #psionics-panel input, #psionics-panel select')
    .forEach(element => element.disabled = navigationBusy || !psionicReady || element.dataset.retained === 'yes');
}
async function savePsionics(choices, source = 'psionics') {
  if (navigationBusy || !psionicReady) return;
  lockNavigation(true);
  try {
    await flushSave();
    const result = await request(`/api/characters/${current.id}/${source}`, {revision:current.revision, ...choices});
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
  renderClassPsionics(view);
  psionicReady = true; setPsionicsBusy();
}

function renderClassPsionics(view) {
  const entitlement = view.class_entitlement;
  if (!entitlement) return;
  const section = document.createElement('section'); section.id = 'class-psionics';
  const heading = document.createElement('h3'); heading.textContent = entitlement.name;
  const summary = document.createElement('p');
  summary.textContent = `${entitlement.path} · psychic save target ${view.effective.save_target} · ` +
    Object.values(view.effective.resources).map(row => `${row.name}: ${row.value}`).join(' · ');
  const guidance = document.createElement('p'); guidance.className = 'help';
  guidance.textContent = [...view.effective.guidance, ...entitlement.guidance].join(' ');
  const searchLabel = document.createElement('label'); searchLabel.textContent = 'Find a class power';
  const search = document.createElement('input'); search.type = 'search';
  search.setAttribute('aria-label', 'Find a class power'); searchLabel.append(search);
  const form = document.createElement('form');
  for (const ability of entitlement.catalog) {
    const details = document.createElement('details');
    details.dataset.search = `${ability.name} ${ability.tags.join(' ')}`.toLowerCase();
    const title = document.createElement('summary');
    const input = document.createElement('input'); input.type = 'checkbox'; input.value = ability.id;
    input.checked = entitlement.state.abilities.selections.includes(ability.id);
    const known = (entitlement.known_abilities || []).includes(ability.id);
    if (known) { input.checked = true; input.dataset.retained = 'yes'; }
    const learned = entitlement.state.learning_levels?.[ability.id];
    if (learned > current.level) input.dataset.retained = 'yes';
    input.setAttribute('aria-label', `Class power: ${ability.name}`);
    input.onclick = event => event.stopPropagation();
    const cost = entitlement.choice_costs[ability.id] || 1;
    title.append(input, document.createTextNode(` ${ability.name} · ` +
      (known ? 'always known' : `${cost} choice${cost === 1 ? '' : 's'}`)));
    const description = document.createElement('p'); description.textContent = ability.description;
    const metadata = document.createElement('p'); metadata.className = 'help';
    metadata.textContent = (ability.parameters || []).map(row => `${row.name}: ${row.text}`).join(' · ');
    const proof = document.createElement('p'); proof.className = 'help';
    proof.textContent = `${ability.source.book} · ${ability.source.section}`;
    const selected = entitlement.abilities.find(row => row.id === ability.id);
    if (learned !== undefined) {
      metadata.textContent += ` · Learned at level ${learned}`;
      if (learned > current.level) metadata.textContent += ' · Available again when that level is attained';
    }
    const requirements = document.createElement('p'); requirements.className = 'help';
    requirements.textContent = (selected?.requirements || []).map(row => row.text +
      (row.satisfied ? ' (met)' : ' (still needed)')).join(' · ');
    details.append(title, description, metadata, requirements, proof); form.append(details);
  }
  const submit = document.createElement('button'); submit.type = 'submit';
  submit.textContent = 'Save class power choices'; form.append(submit);
  form.onsubmit = event => {
    event.preventDefault();
    savePsionics({selections:[...form.querySelectorAll('input:checked')].map(row => row.value)}, 'class-psionics');
  };
  search.oninput = () => {
    const query = search.value.toLowerCase().trim();
    form.querySelectorAll('details').forEach(row => row.hidden = !row.dataset.search.includes(query));
  };
  section.append(heading, summary, guidance, searchLabel, form); $('psionics-panel').append(section);
}
