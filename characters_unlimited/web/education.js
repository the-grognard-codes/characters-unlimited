'use strict';
let educationReady = false, educationLoadSequence = 0;

function setEducationBusy() {
  document.querySelectorAll('#education-panel select, #education-panel button').forEach(element => element.disabled = navigationBusy || !educationReady);
}

function educationLine(text) {
  const item = document.createElement('li'); item.textContent = text; return item;
}

async function loadEducation(character) {
  const sequence = ++educationLoadSequence;
  educationReady = false; setEducationBusy();
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
  educationReady = true; setEducationBusy();
}

function wireEducationEvents() {
  $('education-choose').onclick = () => characterAction('education', {method:'choose', education_id:$('education-choice').value}).catch(showError);
  $('education-roll').onclick = () => characterAction('education', {method:'roll'}).catch(showError);
}
