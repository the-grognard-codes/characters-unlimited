'use strict';
let gamePacks = [], token, current, characters = [], saveTimer, savePromise, navigationBusy = false, coverage;
let requiredFormCharacter, requiredDirtyFlag = false;
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
  setEducationBusy();
  ['name', 'notes', 'new-character', 'source-coverage', 'reroll-ones', 'extra-die', 'reroll-all', 'roll-history', 'import-character', 'backup-characters', 'duplicate-character', 'export-character', 'preview-rule-update', 'export-pdf'].forEach(id => $(id).disabled = busy);
  if (current?.game === 'heroes-unlimited') $('export-pdf').disabled = true;
  document.querySelectorAll('#library button, .attribute button').forEach(button => button.disabled = busy);
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button, #combat-controls select, #combat-controls button, #combat-list button, #required-skill-form input, #required-skill-form textarea, #required-skill-form select, #required-skill-form button').forEach(element => element.disabled = busy || !skillsReady);
  setResourcesBusy();
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
  const pack = gamePacks.find(entry => entry.game === character.game);
  const heroes = character.game === 'heroes-unlimited';
  $('resources-panel').hidden = heroes;
  $('game-title').textContent = heroes ? 'HEROES UNLIMITED · REVISED SECOND EDITION' : 'RIFTS · ULTIMATE EDITION';
  $('class-label').textContent = pack.class_label || 'Occupational character class';
  for (const [element, entries, selected] of [[$('race'),pack.races,character.race],[$('character-class'),pack.classes,character.character_class]]) {
    element.replaceChildren(...entries.map(entry => { const option = document.createElement('option'); option.value = entry.id; option.textContent = entry.name; return option; }));
    element.value = selected; element.disabled = true;
  }
  $('summary-identity').textContent = `${pack.races.find(entry => entry.id === character.race).name} · ${pack.classes.find(entry => entry.id === character.character_class).name} · Level ${character.level}`;
  $('skill-form').closest('section').hidden = heroes;
  $('combat-controls').closest('section').hidden = heroes;
  $('heroes-pending').hidden = !heroes;
  $('education-panel').hidden = !heroes;
  $('export-pdf').disabled = heroes || navigationBusy;
  $('preview-rule-update').disabled = navigationBusy;
  $('name').value = character.name; $('notes').value = character.notes;
  $('summary-name').textContent = character.name || 'Unnamed adventurer';
  $('rule-versions').textContent = `Rules: ${character.rules.id} ${character.rules.version} · ` + Object.entries(character.additional_rule_packs || {}).map(([id, version]) => `${id} ${version}`).join(' · ');
  $('reroll-ones').checked = character.generation?.reroll_ones || false;
  $('extra-die').checked = character.generation?.extra_die || false;
  $('attributes').replaceChildren();
  Object.entries(character.attributes).forEach(([name, attribute]) => {
    const detail = document.createElement('details'); detail.className = 'attribute'; detail.dataset.attribute = name; detail.open = expanded.has(name);
    const heading = document.createElement('summary'); heading.textContent = name;
    const value = document.createElement('strong'); value.textContent = attribute.value; heading.append(value);
    const explanation = document.createElement('p');
    explanation.textContent = `Dice: ${attribute.rolls.join(' + ')}${attribute.discarded?.length ? '; dropped: ' + attribute.discarded.join(' + ') : ''}${attribute.bonus_rolls.length ? '; exceptional: ' + attribute.bonus_rolls.join(' + ') : ''}. Base: ${attribute.base}. ${attribute.explanation.source.book} — ${attribute.explanation.source.section}`;
    for (const modifier of attribute.modifiers || []) {
      explanation.textContent += ` · ${modifier.id.startsWith('physical:') ? modifier.source.section : 'O.C.C. bonus'}: +${modifier.value}${modifier.rolls.length ? ' (dice: ' + modifier.rolls.join(' + ') + ')' : ''} · ${modifier.source.book}, pp. ${modifier.source.pages.join(', ')}`;
    }
    if (attribute.cap != null) explanation.textContent += ` · Normal automatic ceiling: ${attribute.cap}; full raw total retained. Manual values remain available.`;
    if (attribute.fixed != null) explanation.textContent += ` · Fixed total: ${attribute.fixed}; calculated contributions remain recorded.`;
    else if (attribute.adjustment) explanation.textContent += ` · Player adjustment: ${attribute.adjustment}.`;
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
  if (heroes) { ++skillLoadSequence; skillsReady = false; requiredDirtyFlag = false; loadEducation(character).catch(showError); }
  else { ++educationLoadSequence; educationReady = false; loadSkills(character).catch(showError); }
}
let skillsReady = false, skillLoadSequence = 0, skillCatalog = [];
function filterSkillChoices() {
  const previous = $('skill-choice').value;
  const category = $('skill-category').value;
  const matches = skillCatalog.filter(skill => !category || (skill.category || 'domestic') === category);
  $('skill-choice').replaceChildren(...matches.map(skill => { const option = document.createElement('option'); option.value = skill.id; option.textContent = skill.name; return option; }));
  if (matches.some(skill => skill.id === previous)) $('skill-choice').value = previous;
}
$('skill-category').onchange = filterSkillChoices;
async function loadSkills(character) {
  const sequence = ++skillLoadSequence;
  skillsReady = false;
  setResourcesBusy();
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button, #combat-controls select, #combat-controls button, #combat-list button, #required-skill-form input, #required-skill-form textarea, #required-skill-form select, #required-skill-form button').forEach(element => element.disabled = true);
  const view = await request(`/api/characters/${character.id}/skills`);
  if (current.id !== character.id || sequence !== skillLoadSequence) return;
  renderCombat(view.combat);
  renderResources(view.resources);
  skillCatalog = view.catalog;
  const category = $('skill-category').value;
  const categories = ['', ...new Set(view.catalog.map(skill => skill.category || 'domestic'))];
  $('skill-category').replaceChildren(...categories.map(value => { const option = document.createElement('option'); option.value = value; option.textContent = value ? value[0].toUpperCase() + value.slice(1) : 'All reviewed categories'; return option; }));
  if (categories.includes(category)) $('skill-category').value = category;
  filterSkillChoices();
  $('skill-counts').textContent = Object.entries(view.remaining).map(([pool, count]) => `${pool}: ${count} remaining`).join(' · ');
  $('required-skill-form').hidden = !view.required_catalog;
  $('required-skill-counts').hidden = !view.required_catalog;
  if (view.required_catalog) {
    $('required-skill-counts').textContent = Object.entries(view.required_remaining).map(([name,count]) => `${name.replaceAll('_',' ')}: ${count} remaining`).join(' · ');
    if (!requiredNeedsSave()) {
      const choices = character.required_skill_choices || {};
      $('required-native').value = choices.native_language || '';
      $('required-languages').value = (choices.other_languages || []).join('\n');
      for (const name of ['pilot', 'repair']) {
        const blank = document.createElement('option'); blank.value = ''; blank.textContent = 'Choose one…';
        $('required-' + name).replaceChildren(blank, ...view.required_catalog[name].options.map(skill => { const option = document.createElement('option'); option.value = skill.id; option.textContent = skill.name; return option; }));
        $('required-' + name).value = choices[name] || '';
      }
      requiredDirtyFlag = false;
    }
    requiredFormCharacter = current.id;
  }
  $('skill-list').replaceChildren(...[...view.grants.map(skill => ({...skill, grant:true})), ...view.selected].map((skill, index) => {
    const row = document.createElement('details'); const heading = document.createElement('summary');
    heading.textContent = `${skill.name}${skill.specialty ? ' — ' + skill.specialty : ''}${skill.kind === 'physical' ? ' · Physical bonuses' : ': ' + skill.percentage + '%'} · ${skill.grant ? 'O.C.C. grant' : skill.pool} · ${skill.quality}`;
    const explanation = document.createElement('p'); explanation.className = 'help';
    explanation.textContent = skill.kind === 'physical'
      ? Object.entries(skill.effects).flatMap(([group, effects]) => Object.entries(effects).map(([name, effect]) => {
          const value = typeof effect === 'object' ? effect.value : effect;
          const dice = typeof effect === 'object' && effect.rolls.length
            ? ` (dice: ${effect.rolls.join(' + ')})` : '';
          const pending = group === 'resources'
            ? (view.resources?.generated ? ' bonus to starting total' : ' bonus; starting total not generated') : '';
          return `${name.replaceAll('_', ' ')} +${value}${dice}${pending}`;
        })).join(' · ')
      : Object.entries(skill.contributions).map(([name, amount]) => `${name.replaceAll('_', ' ')} ${amount}%`).join(' + ');
    explanation.textContent += ` · ${skill.source.book}, pp. ${skill.source.pages.join(', ')}`;
    if (view.intelligence_source && skill.kind !== 'physical') explanation.textContent += ` · I.Q. chart: ${view.intelligence_source.book}, pp. ${view.intelligence_source.pages.join(', ')}`;
    if (skill.uncapped_percentage > 98) explanation.textContent += ` · Capped at 98% from ${skill.uncapped_percentage}% (Ultimate Edition, p. 301).`;
    for (const check of skill.additional_checks || []) {
      const total = Object.entries(check.contributions).map(([name,amount]) => `${name.replaceAll('_',' ')} ${amount}%`).join(' + ');
      if (check.multiplier != null && check.multiplier !== 1) explanation.textContent += ` · ${check.name} uses normal proficiency ${check.normal_percentage}% × ${check.multiplier}.`;
      explanation.textContent += ` · ${check.name}: ${check.percentage}% (${total}${check.uncapped_percentage > 98 ? '; capped at 98%' : ''})`;
    }
    if (skill.notes) explanation.textContent += ' · ' + skill.notes.join(' ');
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
  setResourcesBusy();
  document.querySelectorAll('#skill-form input, #skill-form select, #skill-form button, #skill-list button, #combat-controls select, #combat-controls button, #combat-list button, #required-skill-form input, #required-skill-form textarea, #required-skill-form select, #required-skill-form button').forEach(element => element.disabled = navigationBusy);
}
wireCombatEvents();
wireEducationEvents();
function readRequiredChoices() {
  return {native_language:$('required-native').value.trim(), pilot:$('required-pilot').value, repair:$('required-repair').value,
    other_languages:$('required-languages').value.trim() ? $('required-languages').value.split(/\r?\n/).map(value => value.trim()) : []};
}
function requiredNeedsSave() {
  if (!current || requiredFormCharacter !== current.id || !requiredDirtyFlag || $('required-skill-form').hidden) return false;
  const choices = readRequiredChoices(), saved = current.required_skill_choices || {};
  return ['native_language','pilot','repair'].some(name => choices[name] !== (saved[name] || '')) || JSON.stringify(choices.other_languages) !== JSON.stringify(saved.other_languages || []);
}
$('required-skill-form').onsubmit = async event => {
  event.preventDefault(); if (navigationBusy || !skillsReady) return;
  lockNavigation(true);
  try { await flushSave(); } catch(error) { showError(error); } finally { lockNavigation(false); }
};
$('skill-form').onsubmit = async event => {
  event.preventDefault();
  if (!skillsReady || navigationBusy) return;
  await characterAction('skills', {selections:[...(current.skill_selections || []), {skill_id:$('skill-choice').value, pool:$('skill-pool').value, specialty:$('skill-specialty').value}]}).catch(showError);
};
let rulePreview;
$('preview-rule-update').onclick = async () => {
  if (navigationBusy || !current) return;
  lockNavigation(true);
  try {
    await flushSave();
    const preview = await request(`/api/characters/${current.id}/rule-preview`, {});
    rulePreview = {...preview, characterId:current.id};
    $('rule-error').hidden = true;
    $('rule-update-summary').textContent = preview.changes.length ? preview.changes.map(change => `${change.pack_id}: ${change.from} → ${change.to}`).join(' · ') : 'This character already uses the active rules covered by this preview.';
    $('rule-update-scope').textContent = preview.scope + ' A backup of all characters is created before applying.';
    $('rule-update-skills').replaceChildren(...preview.skills.map(skill => {
      const row = document.createElement('li'); const unit = skill.unit ?? '%'; row.textContent = `${skill.name}${skill.specialty ? ' — ' + skill.specialty : ''}: ${skill.before == null ? 'Not yet granted' : skill.before + unit} → ${skill.after == null ? 'Removed' : skill.after + unit}`; return row;
    }));
    $('rule-update-combat').replaceChildren(...rulePreview.combat.map(row => { const item = document.createElement('li'); item.textContent = `${row.name}: ${row.before ?? 'not available'} → ${row.after ?? 'not available'}`; return item; }));
    $('rule-update-counts').textContent = Object.keys(preview.before_remaining).map(pool => `${pool} remaining: ${preview.before_remaining[pool]} → ${preview.after_remaining[pool]}`).join(' · ');
    $('rule-update-counts').textContent += Object.keys(preview.after_required_remaining).length ? ' · Required choices: ' + Object.keys(preview.after_required_remaining).map(name => `${name.replaceAll('_',' ')}: ${preview.before_required_remaining[name] ?? 'not yet supported'} → ${preview.after_required_remaining[name]}`).join(' · ') : '';
    $('rule-update-findings').replaceChildren(...[...preview.gaps, ...preview.sources].map(message => { const row = document.createElement('li'); row.textContent = message; return row; }));
    $('apply-rule-update').disabled = !preview.changes.length;
    $('rule-update-dialog').showModal();
  } catch (error) { showError(error); } finally { lockNavigation(false); }
};
$('cancel-rule-update').onclick = () => $('rule-update-dialog').close();
$('apply-rule-update').onclick = async () => {
  if (navigationBusy || !rulePreview?.changes.length) return;
  lockNavigation(true); $('apply-rule-update').disabled = true; $('cancel-rule-update').disabled = true;
  try {
    const result = await request(`/api/characters/${rulePreview.characterId}/rule-upgrade`, {revision:rulePreview.revision, token:rulePreview.token});
    render(result.character); $('rule-update-dialog').close();
    $('transfer-status').textContent = `Rules updated. Before-update backup: ${result.backup.path}`;
  } catch (error) { $('rule-error').textContent = error.message; $('rule-error').hidden = false; }
  finally { lockNavigation(false); $('apply-rule-update').disabled = false; $('cancel-rule-update').disabled = false; }
};
async function transfer(action) {
  if (navigationBusy) return;
  lockNavigation(true); $('transfer-status').textContent = '';
  try { await flushSave(); await action(); }
  catch(error) { showError(error); }
  finally { lockNavigation(false); }
}
$('duplicate-character').onclick = () => transfer(async () => {
  render(await request(`/api/characters/${current.id}/duplicate`, {}));
  $('transfer-status').textContent = 'Independent copy saved on this PC.';
});
$('export-character').onclick = () => transfer(async () => {
  const bundle = await request(`/api/characters/${current.id}/export`);
  const url = URL.createObjectURL(new Blob([JSON.stringify(bundle)], {type:'application/json'}));
  const link = document.createElement('a'); link.href = url; link.download = `characters-unlimited-${current.id}.json`;
  document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  $('transfer-status').textContent = 'Portable save download requested. It includes the exact supported rule definitions.';
});
$('backup-characters').onclick = () => transfer(async () => {
  const backup = await request('/api/backups', {});
  $('transfer-status').textContent = `Backup saved: ${backup.path}`;
});
$('import-character').onclick = () => $('import-file').click();
$('import-file').onchange = () => transfer(async () => {
  const file = $('import-file').files[0]; $('import-file').value = '';
  if (!file) return;
  if (file.size > 12_000_000) throw new Error('Choose a portable JSON save below 12 MB.');
  let bundle;
  try { bundle = JSON.parse(await file.text()); }
  catch { throw new Error('This file is not valid JSON. Choose a portable character save.'); }
  render(await request('/api/import', {bundle}));
  $('transfer-status').textContent = 'Portable save imported as a new character. Existing characters were retained.';
});
async function flushSave() {
  clearTimeout(saveTimer);
  if (savePromise) return savePromise;
  savePromise = (async () => {
    let skillsChanged = false;
    while (current && ($('name').value !== current.name || $('notes').value !== current.notes || requiredNeedsSave())) {
      $('save-status').textContent = 'Saving…';
      const changes = {revision: current.revision ?? 0};
      if ($('name').value !== current.name) changes.name = $('name').value;
      if ($('notes').value !== current.notes) changes.notes = $('notes').value;
      let saved;
      if (changes.name !== undefined || changes.notes !== undefined) saved = await request('/api/characters/' + current.id, changes);
      else { saved = await request(`/api/characters/${current.id}/required-skills`, {...changes, choices:readRequiredChoices()}); skillsChanged = true; }
      current = saved; characters = [saved, ...characters.filter(item => item.id !== saved.id)];
      $('summary-name').textContent = saved.name || 'Unnamed adventurer'; library();
    }
    $('save-status').textContent = 'Saved on this PC';
    if (skillsChanged) loadSkills(current).catch(showError);
  })();
  try { await savePromise; } finally { savePromise = null; }
}
['name','notes','required-native','required-languages','required-pilot','required-repair'].forEach(id => $(id).oninput = () => { if (id.startsWith('required-')) requiredDirtyFlag = true; $('save-status').textContent = 'Unsaved changes'; clearTimeout(saveTimer); saveTimer = setTimeout(() => flushSave().catch(showError), 400); });
window.addEventListener('beforeunload', event => { if (current && ($('name').value !== current.name || $('notes').value !== current.notes || requiredNeedsSave())) { event.preventDefault(); event.returnValue = ''; } });
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
        for (const modifier of value.modifiers || []) {
            text.textContent += ` · ${modifier.id.startsWith('physical:') ? modifier.source.section : 'O.C.C. contribution'} +${modifier.value}${modifier.rolls.length ? ' (dice: ' + modifier.rolls.join(', ') + ')' : ''}`;
        }
    }
    return entry;
  }));
  $('history-dialog').showModal();
};
$('history-close').onclick = () => $('history-dialog').close();
function renderCoverageOptions() {
  const query = $('option-search').value.toLowerCase();
  const matches = coverage.options.filter(entry => `${entry.name} ${entry.aliases.join(' ')} ${entry.book_id}`.toLowerCase().includes(query));
  $('option-count').textContent = `${matches.length} canonical option identities. Mechanics and dependency review remain pending.`;
  $('coverage-options').replaceChildren(...matches.map(entry => {
    const row = document.createElement('details'); row.className = 'source-entry';
    const title = document.createElement('summary'); title.textContent = `${entry.name} · ${entry.kind.toUpperCase()} · ${entry.identity_review} identity`;
    const status = document.createElement('p'); status.className = 'help';
    status.textContent = `${entry.game} · ${entry.book_id} · mechanics: ${entry.mechanical_review} · dependencies: ${entry.dependency_review} · automation: ${entry.automation}`;
    const source = document.createElement('p'); source.className = 'help';
    const sections = entry.candidate_ids.map(id => coverage.candidates.find(candidate => candidate.id === id)).map(candidate => `Markdown lines ${candidate.line}–${candidate.end_line}`).join('; ');
    source.textContent = `Identity evidence: printed pp. ${entry.source.printed_pages.join(', ')} / PDF pp. ${entry.source.pdf_pages.join(', ')} · ${sections}`;
    const tickets = document.createElement('p'); tickets.className = 'help';
    tickets.textContent = `Implementation tickets: ${entry.tickets.length ? entry.tickets.map(id => {
      const ticket = (coverage.content_tickets || []).find(item => item.id === id);
      return ticket ? `${ticket.id}: ${ticket.title}` : id;
    }).join('; ') : 'Awaiting named content batch'}. Assignment does not certify implementation.`;
    row.append(title, status, source, tickets);
    if (entry.dependencies.length) { const dependencies = document.createElement('p'); dependencies.className = 'help'; dependencies.textContent = 'Recorded dependencies: ' + entry.dependencies.map(id => coverage.options.find(option => option.id === id).name).join(' · ') + '. Complete dependency review remains pending.'; row.append(dependencies); }
    if (entry.aliases.length) { const aliases = document.createElement('p'); aliases.className = 'help'; aliases.textContent = 'Aliases: ' + entry.aliases.join(' · '); row.append(aliases); }
    for (const finding of entry.findings) { const note = document.createElement('p'); note.className = 'help'; note.textContent = finding; row.append(note); }
    return row;
  }));
}
$('option-search').oninput = renderCoverageOptions;
function renderCoverageCandidates() {
  const query = $('coverage-search').value.toLowerCase();
  const matches = coverage.candidates.filter(item => `${item.title} ${item.book_id}`.toLowerCase().includes(query));
  $('coverage-count').textContent = `${matches.length} candidate sections. Showing the first 100; search to narrow results.`;
  $('coverage-candidates').replaceChildren(...matches.slice(0,100).map(item => {
    const entry = document.createElement('details'); entry.className = 'source-entry';
    const title = document.createElement('summary'); title.textContent = item.title;
    const description = document.createElement('p'); description.className = 'help';
    description.textContent = `${item.book_id} · Markdown lines ${item.line}–${item.end_line} · ${item.status}. Mechanical implementation and source review remain pending.`;
    entry.append(title,description);
    for (const gap of item.source_gaps || []) {
      const warning = document.createElement('p'); warning.textContent = `Source gap at Markdown lines ${gap.line}–${gap.end_line}: ${gap.description}`; entry.append(warning);
    }
    return entry;
  }));
}
$('coverage-search').oninput = renderCoverageCandidates;
$('source-coverage').onclick = async () => {
  if (navigationBusy) return;
  lockNavigation(true);
  try {
    await flushSave(); coverage = await request('/api/coverage');
    $('builder').hidden = true; $('welcome').hidden = true; $('coverage').hidden = false;
    $('coverage-summary').textContent = `${coverage.summary.books} books · ${coverage.summary.candidates} extracted sections · ${coverage.summary.books_reviewed} books reviewed · ${coverage.summary.canonical_options} canonical identities · ${coverage.summary.identity_confirmed} identities confirmed · ${coverage.summary.mechanically_reviewed} mechanically reviewed · ${coverage.summary.content_tickets || 0} content tickets · ${coverage.summary.unassigned_options} awaiting content tickets · ${coverage.summary.fully_automated} fully automated options · ${coverage.summary.source_gaps || 0} source gaps`;
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
      entry.append(title,metadata,fingerprints);
      for (const gap of book.source_gaps || []) {
        const warning = document.createElement('p'); warning.textContent = `Source gap at Markdown lines ${gap.line}–${gap.end_line}: ${gap.description}`; entry.append(warning);
      }
      return entry;
    }));
    $('audit-findings').replaceChildren(...coverage.audit_findings.map(message => { const item = document.createElement('li'); item.textContent = message; return item; }));
    renderCoverageOptions(); renderCoverageCandidates();
  } catch(error) { showError(error); } finally { lockNavigation(false); }
};
$('export-pdf').onclick = async () => {
  if (navigationBusy) return;
  lockNavigation(true);
  try {
    await flushSave();
    $('pdf-export-checklist').replaceChildren(...current.completion.map(message => {
      const item = document.createElement('li'); item.textContent = message; return item;
    }));
    $('pdf-export-error').hidden = true;
    $('pdf-export-dialog').showModal();
  } catch(error) { showError(error); lockNavigation(false); }
};
$('pdf-export-dialog').addEventListener('close', () => lockNavigation(false));
$('pdf-export-cancel').onclick = () => $('pdf-export-dialog').close();
$('pdf-export-download').onclick = async () => {
  const button = $('pdf-export-download'); button.disabled = true;
  try {
    const response = await fetch('/api/characters/' + current.id + '/pdf');
    if (!response.ok) throw new Error((await response.json()).error || 'PDF export failed');
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a'); link.href = url;
    link.download = 'rifts-character-sheet.pdf'; document.body.append(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    $('pdf-export-dialog').close();
  } catch(error) {
    $('pdf-export-error').textContent = error.message; $('pdf-export-error').hidden = false;
  } finally { button.disabled = false; }
};
$('create-form').onsubmit = async event => { event.preventDefault(); const button = event.submitter; button.disabled = true; try { render(await request('/api/characters', {name:new FormData(event.target).get('name'), game:$('new-game').value, generation:{reroll_ones:$('new-reroll-ones').checked, extra_die:$('new-extra-die').checked}})); $('new-dialog').close(); event.target.reset(); } catch(error) { $('create-error').textContent = error.message; $('create-error').hidden = false; } finally { button.disabled = false; } };
function updateNewIdentity() {
  const pack = gamePacks.find(entry => entry.game === $('new-game').value);
  $('new-identity').textContent = `${pack.name || 'Rifts Ultimate Edition'} · ${pack.races[0].name} · ${pack.classes[0].name}. Initial attributes follow the core book. Other creation paths remain unfinished.`;
}
$('new-game').onchange = updateNewIdentity;
wireResourcesEvents();
request('/api/bootstrap').then(result => {
  token = result.token; characters = result.characters; gamePacks = result.catalog.packs;
  $('new-game').replaceChildren(...result.catalog.games.map(game => { const option = document.createElement('option'); option.value = game.id; option.textContent = game.name; return option; }));
  updateNewIdentity(); library();
}).catch(showError);
