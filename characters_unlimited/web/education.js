'use strict';
let educationReady = false, educationLoadSequence = 0;
let heroProgramView = null;

function setEducationBusy() {
  document.querySelectorAll('#education-panel select, #education-panel button').forEach(element => element.disabled = navigationBusy || !educationReady);
  document.querySelectorAll('#hero-program-form select, #hero-program-form button').forEach(element => element.disabled = navigationBusy || !educationReady || !heroProgramView?.slots.length);
  document.querySelectorAll('#hero-secondary-form select, #hero-secondary-form button').forEach(element => element.disabled = navigationBusy || !educationReady || !heroProgramView?.secondary.supported || !current.education);
}

function educationLine(text) {
  const item = document.createElement('li'); item.textContent = text; return item;
}

async function loadEducation(character) {
  const sequence = ++educationLoadSequence;
  educationReady = false; setEducationBusy();
  heroProgramView = null;
  for (const id of ['hero-program-list', 'hero-program-skills', 'hero-program-guidance', 'hero-program-warnings', 'hero-secondary-list', 'hero-secondary-guidance']) $(id).replaceChildren();
  $('education-result').textContent = 'Loading education…';
  $('education-details').replaceChildren(); $('education-history').replaceChildren();
  const view = await request(`/api/characters/${character.id}/education`);
  if (current.id !== character.id || sequence !== educationLoadSequence) return;
  $('education-choice').replaceChildren(...view.catalog.map(outcome => {
    const option = document.createElement('option'); option.value = outcome.id; option.textContent = outcome.name; return option;
  }));
  $('education-choice').value = view.selection?.id || view.catalog[0].id;
  const outcome = view.outcome;
  $('education-result').textContent = outcome ? `${outcome.name} · ${view.selection.method === 'roll' ? 'Rolled ' + view.selection.roll : 'Chosen by player'} · ${outcome.secondary_count} Secondary skills allowed` : 'Choose or roll education to save its outcome. No education selected yet.';
  const details = [];
  if (outcome) {
    for (const slot of outcome.program_slots) details.push(`${slot.name}: ${slot.bonus == null ? 'no percentage bonus specified' : '+' + slot.bonus + '% scholastic bonus'}. ${slot.restriction}.`);
    for (const grant of outcome.street_grants || []) details.push(grant);
    for (const [category, count] of Object.entries(outcome.street_choices || {})) details.push(`${category}: ${count} Street choices allowed`);
    details.push(...view.universal_grants.map(grant => 'Universal skill: ' + grant), ...(outcome.guidance || []));
  }
  details.push(...view.guidance);
  details.push(`${view.source.book}, printed pp. ${view.source.pages.join(', ')} (PDF pp. ${view.source.pdf_pages.join(', ')}). ${view.rules.id} ${view.rules.version}${view.selection ? ' · pinned to this character' : ' · selecting education pins these rules'}.`);
  $('education-details').replaceChildren(...details.map(educationLine));
  $('education-history').replaceChildren(...view.history.map(selection => educationLine(`${view.catalog.find(item => item.id === selection.id).name} · ${selection.method === 'roll' ? 'roll ' + selection.roll : 'player choice'}`)));
  const programs = await request(`/api/characters/${character.id}/hero-programs`);
  if (current.id !== character.id || sequence !== educationLoadSequence) return;
  heroProgramView = programs;
  $('hero-program-choice').replaceChildren(...programs.catalog.map(program => {
    const option = document.createElement('option'); option.value = program.id; option.textContent = program.name; return option;
  }));
  $('hero-program-slot').replaceChildren(...programs.slots.map((slot, index) => {
    const option = document.createElement('option'); option.value = index;
    option.textContent = `${slot.name} (${slot.bonus == null ? 'no bonus specified' : '+' + slot.bonus + '%'}) · ${slot.restriction}`; return option;
  }));
  $('hero-program-choice').onchange = () => {
    const program = programs.catalog.find(item => item.id === $('hero-program-choice').value);
    const eligible = program.eligible_slots[view.selection?.id]?.[0] ?? -1;
    if (eligible >= 0) $('hero-program-slot').value = eligible;
  };
  $('hero-program-choice').onchange();
  $('hero-program-list').replaceChildren(...programs.selections.map((selection, index) => {
    const item = educationLine(`${programs.catalog.find(program => program.id === selection.program).name} · slot ${selection.slot + 1}`);
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Remove';
    button.onclick = () => characterAction('hero-programs', {selections:heroProgramView.selections.filter((_, i) => i !== index)}).catch(showError);
    item.append(button); return item;
  }));
  $('hero-program-skills').replaceChildren(...programs.skills.map(skill => {
    const item = educationLine(`${skill.name}: ${skill.percentage}% (+${skill.per_level}% per level) · base ${skill.contributions.base}, education +${skill.contributions.education}, I.Q. +${skill.contributions.intelligence}`);
    const detail = document.createElement('small'); detail.textContent = ` ${skill.category}; printed pp. ${skill.source.pages.join(', ')} / PDF pp. ${skill.source.pdf_pages.join(', ')}${skill.prerequisites.length ? '; requires ' + skill.prerequisites.join(', ') : ''}${skill.secondary_selected ? '; selected as Secondary (no added education bonus)' : ''}`;
    item.append(detail); return item;
  }));
  $('hero-program-warnings').replaceChildren(...programs.warnings.map(educationLine));
  $('hero-program-warnings').hidden = !programs.warnings.length;
  $('hero-program-guidance').replaceChildren(...[...programs.guidance,
    `${programs.rules.id} ${programs.rules.version} · ${programs.pinned ? 'pinned to this character' : 'preview; saving program choices pins these rules'}`].map(educationLine));
  const secondary = programs.secondary;
  $('hero-secondary-counts').textContent = secondary.supported ? `${secondary.used} selections used · ${secondary.allowance} allowed · ${secondary.remaining} remaining. Secondary skills receive I.Q. bonuses, with no scholastic bonus.` : 'Review rule updates to add supported Secondary selections to this earlier rule pin.';
  $('hero-secondary-form').hidden = !secondary.supported;
  const categories = [...new Set(secondary.catalog.map(skill => skill.category))];
  $('hero-secondary-category').replaceChildren(...categories.map(category => {
    const option = document.createElement('option'); option.value = category; option.textContent = category; return option;
  }));
  const updateSecondaryChoices = () => {
    $('hero-secondary-choice').replaceChildren(...secondary.catalog.filter(skill => skill.category === $('hero-secondary-category').value).map(skill => {
      const option = document.createElement('option'); option.value = skill.id;
      option.textContent = skill.name + (secondary.eligible_skill_ids.includes(skill.id) ? '' : ' · outside eligible Secondary categories'); return option;
    }));
  };
  $('hero-secondary-category').onchange = updateSecondaryChoices;
  updateSecondaryChoices();
  $('hero-secondary-list').replaceChildren(...secondary.selections.map((identifier,index) => {
    const skill = secondary.catalog.find(item => item.id === identifier);
    const item = educationLine(skill.name);
    const button = document.createElement('button'); button.type = 'button'; button.textContent = 'Remove';
    button.onclick = () => characterAction('hero-secondary',{selections:heroProgramView.secondary.selections.filter((_,i) => i !== index)}).catch(showError);
    item.append(button); return item;
  }));
  const secondaryGuidance = [...secondary.guidance];
  if (secondary.source) secondaryGuidance.push(`${secondary.source.book}, printed pp. ${secondary.source.pages.join(', ')} / PDF pp. ${secondary.source.pdf_pages.join(', ')}.`);
  $('hero-secondary-guidance').replaceChildren(...secondaryGuidance.map(educationLine));
  educationReady = true; setEducationBusy();
}

function wireEducationEvents() {
  $('education-choose').onclick = () => characterAction('education', {method:'choose', education_id:$('education-choice').value}).catch(showError);
  $('education-roll').onclick = () => characterAction('education', {method:'roll'}).catch(showError);
  $('hero-program-form').onsubmit = event => {
    event.preventDefault();
    characterAction('hero-programs', {selections:[...heroProgramView.selections, {slot:Number($('hero-program-slot').value), program:$('hero-program-choice').value}]}).catch(showError);
  };
  $('hero-secondary-form').onsubmit = event => {
    event.preventDefault();
    characterAction('hero-secondary',{selections:[...heroProgramView.secondary.selections,$('hero-secondary-choice').value]}).catch(showError);
  };
}
